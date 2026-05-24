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
    def __init__(self, files: List[tuple], mode="compress"):
        self.id = str(uuid.uuid4())
        self.mode = mode  # "compress" or "webp"
        self.files = files  # list of (filename, bytes)
        self.name_map = {}  # original -> new
        self.status = TaskStatus.QUEUED
        self.progress = 0
        self.results = {}  # filename -> compressed bytes
        self.error = None
        self.file_progress = {filename: 0 for filename, _ in files}
        self.compressed_sizes = {}  # filename -> bytes


class CompressionQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.tasks: Dict[str, CompressionTask] = {}

    async def add_task(self, files: List[tuple], mode="compress") -> str:
        task = CompressionTask(files, mode)
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

                    # --- TRYB WEBP ---
                    if task.mode == "webp":
                        from services.compress import auto_convert_to_webp
                        compressed = auto_convert_to_webp(data, filename)
                        new_filename = filename.rsplit(".", 1)[0] + ".webp"
                        print("webp-new_filename", new_filename)

                    # --- TRYB NORMALNEJ KOMPRESJI ---
                    else:
                        from services.compress import auto_compress
                        compressed = auto_compress(data, filename)
                        new_filename = filename

                    # zapisujemy wynik
                    task.results[new_filename] = compressed
                    task.compressed_sizes[new_filename] = len(compressed)

                    # mapowanie nazw (ORYGINAŁ → NOWA NAZWA)
                    task.name_map[filename] = new_filename

                    # progres
                    task.file_progress[new_filename] = 100
                    task.progress = int(((idx + 1) / total) * 100)

                task.status = TaskStatus.DONE

            except Exception as e:
                task.status = TaskStatus.ERROR
                task.error = str(e)

            self.queue.task_done()



    # async def worker(self):
    #     while True:
    #         task: CompressionTask = await self.queue.get()
    #         task.status = TaskStatus.PROCESSING

    #         try:
    #             total = len(task.files)

    #             for idx, (filename, data) in enumerate(task.files):

    #                 if task.mode == "webp":
    #                     from services.compress import auto_convert_to_webp
    #                     compressed = auto_convert_to_webp(data, filename)
    #                     new_filename = filename.rsplit(".", 1)[0] + ".webp"
    #                 else:
    #                     from services.compress import auto_compress
    #                     compressed = auto_compress(data, filename)
    #                     new_filename = filename

    #                 task.results[new_filename] = compressed
    #                 task.compressed_sizes[new_filename] = len(compressed)

    #                 task.file_progress[new_filename] = 100
    #                 task.progress = int(((idx + 1) / total) * 100)

    #             task.status = TaskStatus.DONE

    #         except Exception as e:
    #             task.status = TaskStatus.ERROR
    #             task.error = str(e)

    #         self.queue.task_done()


    

    def build_zip(self, task: CompressionTask) -> bytes:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, data in task.results.items():
                zipf.writestr(filename, data)
        return buffer.getvalue()


compression_queue = CompressionQueue()
