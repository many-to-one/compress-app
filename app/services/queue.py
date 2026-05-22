# FILE: services/queue.py
import asyncio
import uuid
from typing import Dict, List
from services.compress import auto_compress
import zipfile
from io import BytesIO

class TaskStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class CompressionTask:
    def __init__(self, files: List[tuple]):
        self.id = str(uuid.uuid4())
        self.files = files  # list of (filename, bytes)
        self.status = TaskStatus.QUEUED
        self.progress = 0
        self.results = {}  # filename -> compressed bytes
        self.error = None


class CompressionQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.tasks: Dict[str, CompressionTask] = {}

    async def add_task(self, files: List[tuple]) -> str:
        task = CompressionTask(files)
        self.tasks[task.id] = task
        await self.queue.put(task)
        return task.id

    def get_task(self, task_id: str) -> CompressionTask:
        return self.tasks.get(task_id)

    async def worker(self):
        while True:
            task: CompressionTask = await self.queue.get()
            task.status = TaskStatus.PROCESSING

            try:
                total = len(task.files)
                for idx, (filename, data) in enumerate(task.files):
                    compressed = auto_compress(data, filename)
                    task.results[filename] = compressed
                    task.progress = int(((idx + 1) / total) * 100)

                task.status = TaskStatus.DONE

            except Exception as e:
                task.status = TaskStatus.ERROR
                task.error = str(e)

            self.queue.task_done()

    def build_zip(self, task: CompressionTask) -> bytes:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, data in task.results.items():
                zipf.writestr(filename, data)
        return buffer.getvalue()


compression_queue = CompressionQueue()
