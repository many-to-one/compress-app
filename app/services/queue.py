# # FILE: services/queue.py
# import asyncio
# import uuid
# from typing import Dict, List
# from services.compress import auto_compress
# import zipfile
# from io import BytesIO

# class TaskStatus:
#     QUEUED = "queued"
#     PROCESSING = "processing"
#     DONE = "done"
#     ERROR = "error"


# class CompressionTask:
#     def __init__(self, files: List[tuple], mode="compress"):
#         self.id = str(uuid.uuid4())
#         self.mode = mode  # "compress" or "webp"
#         self.files = files  # list of (filename, bytes)
#         self.name_map = {}  # original -> new
#         self.status = TaskStatus.QUEUED
#         self.progress = 0
#         self.results = {}  # filename -> compressed bytes
#         self.error = None
#         self.file_progress = {filename: 0 for filename, _ in files}
#         self.compressed_sizes = {}  # filename -> bytes


# class CompressionQueue:
#     def __init__(self):
#         self.queue = asyncio.Queue()
#         self.tasks: Dict[str, CompressionTask] = {}

#     async def add_task(self, files: List[tuple], mode="compress") -> str:
#         task = CompressionTask(files, mode)
#         self.tasks[task.id] = task
#         await self.queue.put(task)
#         return task.id

#     def get_task(self, task_id: str) -> CompressionTask:
#         return self.tasks.get(task_id)

#     async def worker(self):
#         while True:
#             task: CompressionTask = await self.queue.get()
#             task.status = TaskStatus.PROCESSING

#             try:
#                 total = len(task.files)

#                 for idx, (filename, data) in enumerate(task.files):

#                     # --- TRYB WEBP ---
#                     if task.mode == "webp":
#                         from services.compress import auto_convert_to_webp
#                         compressed = auto_convert_to_webp(data, filename)
#                         new_filename = filename.rsplit(".", 1)[0] + ".webp"
#                         print("webp-new_filename", new_filename)

#                     # --- TRYB NORMALNEJ KOMPRESJI ---
#                     else:
#                         from services.compress import auto_compress
#                         compressed = auto_compress(data, filename)
#                         new_filename = filename

#                     # zapisujemy wynik
#                     task.results[new_filename] = compressed
#                     task.compressed_sizes[new_filename] = len(compressed)

#                     # mapowanie nazw (ORYGINAŁ → NOWA NAZWA)
#                     task.name_map[filename] = new_filename

#                     # progres
#                     task.file_progress[new_filename] = 100
#                     task.progress = int(((idx + 1) / total) * 100)

#                 task.status = TaskStatus.DONE

#             except Exception as e:
#                 task.status = TaskStatus.ERROR
#                 task.error = str(e)

#             self.queue.task_done()


    

#     def build_zip(self, task: CompressionTask) -> bytes:
#         buffer = BytesIO()
#         with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
#             for filename, data in task.results.items():
#                 zipf.writestr(filename, data)
#         return buffer.getvalue()


# compression_queue = CompressionQueue()






import asyncio
import uuid
import zipfile

from io import BytesIO
from typing import Dict

from services.compress import auto_compress


# =========================
# STATUS
# =========================

class TaskStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


# =========================
# TASK
# =========================

class CompressionTask:

    def __init__(self, files):

        self.id = str(uuid.uuid4())

        self.status = TaskStatus.QUEUED

        self.progress = 0

        self.error = None

        self.files = files

        self.results = {}

        self.file_progress = {}

        self.total_files = len(files)

        self.completed_files = 0

        self.compressed_sizes = {}  # filename -> bytes


# =========================
# QUEUE
# =========================

class CompressionQueue:

    def __init__(self):

        self.queue = asyncio.Queue()

        self.tasks: Dict[str, CompressionTask] = {}

    # =====================
    # ADD TASK
    # =====================

    async def add_task(self, files):

        task = CompressionTask(files)

        self.tasks[task.id] = task

        await self.queue.put(task)

        return task.id

    # =====================
    # GET TASK
    # =====================

    def get_task(self, task_id):

        return self.tasks.get(task_id)

    # =====================
    # WORKER
    # =====================

    async def worker(self):

        while True:

            task = await self.queue.get()

            task.status = TaskStatus.PROCESSING

            try:

                # Uruchamiamy przetwarzanie plików
                for file_data in task.files:
                    await self.process_single_file(task, file_data)
                

                # task.progress = 100

                # task.status = TaskStatus.DONE

                # Tylko jeśli mamy jakiekolwiek wyniki, uznajemy za DONE
                if task.results:
                    task.progress = 100
                    task.status = TaskStatus.DONE
                else:
                    task.status = TaskStatus.ERROR
                    task.error = "All files failed to compress"

            except Exception as e:

                task.status = TaskStatus.ERROR

                task.error = str(e)

            finally:

                self.queue.task_done()

    # =====================
    # SINGLE FILE
    # =====================

    async def process_single_file(self, task, file_data):
        filename = file_data["filename"]
        data = file_data["data"]
        try:
            # Uruchamiamy kompresję (CPU bound) w osobnym wątku!
            compressed = await asyncio.to_thread(auto_compress, data, filename)
            
            task.results[filename] = compressed
            task.compressed_sizes[filename] = len(compressed)
            task.file_progress[filename] = 100
            task.completed_files += 1
            task.progress = int((task.completed_files / task.total_files) * 100)
        except Exception as e:
            print(f"Error compressing {filename}: {e}")


    # =====================
    # ZIP
    # =====================

    def build_zip(self, task) -> BytesIO:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, data in task.results.items():
                zipf.writestr(filename, data)
        zip_buffer.seek(0)
        return zip_buffer