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

        self.size_before = None

        self.compressed_sizes = {}

        self.total_files = len(files)
        self.completed_files = 0

        for file_data in files:
            self.file_progress[file_data["filename"]] = 0


# =========================
# QUEUE
# =========================

class CompressionQueue:

    def __init__(self):

        self.queue = asyncio.Queue()

        self.tasks: Dict[str, CompressionTask] = {}

        # ilu użytkowników jednocześnie
        self.user_semaphore = asyncio.Semaphore(5)

    # =====================
    # ADD TASK
    # =====================

    async def add_task(self, files):

        task = CompressionTask(files)

        self.tasks[task.id] = task
        total_size = sum(len(data) for _, data in files)
        task.size_before = total_size

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

        async def run_task(task):

            async with self.user_semaphore:

                task.status = TaskStatus.PROCESSING

                try:

                    await self.process_batch(task)

                    if task.results:

                        task.progress = 100
                        task.status = TaskStatus.DONE

                    else:

                        task.status = TaskStatus.ERROR
                        task.error = "All files failed"

                except Exception as e:

                    task.status = TaskStatus.ERROR
                    task.error = str(e)

                finally:

                    self.queue.task_done()

        while True:

            task = await self.queue.get()

            asyncio.create_task(run_task(task))

    # =====================
    # BATCH
    # =====================

    async def process_batch(self, task):

        file_semaphore = asyncio.Semaphore(8)

        async def process(file_data):

            async with file_semaphore:

                await self.process_single_file(
                    task,
                    file_data
                )

        jobs = [
            process(file_data)
            for file_data in task.files
        ]

        await asyncio.gather(
            *jobs,
            return_exceptions=True
        )

    # =====================
    # SINGLE FILE
    # =====================

    async def process_single_file(
        self,
        task,
        file_data
    ):

        filename = file_data["filename"]
        data = file_data["data"]

        # print('--------------file_data--------------', len(data)/ 1024 / 1024)

        try:

            compressed = await asyncio.to_thread(
                auto_compress,
                data,
                filename
            )

            task.results[filename] = compressed

            task.compressed_sizes[filename] = len(compressed)

            task.file_progress[filename] = 100

            task.completed_files += 1

            task.size_before += len(data)/ 1024 / 1024

            task.progress = int(
                (task.completed_files / task.total_files) * 100
            )

        except Exception as e:

            print(
                f"Compression error {filename}: {e}"
            )

    # =====================
    # ZIP
    # =====================

    def build_zip(self, task):

        zip_buffer = BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            for filename, data in task.results.items():

                zipf.writestr(
                    filename,
                    data
                )

        zip_buffer.seek(0)

        return zip_buffer



# =========================================================================================================

# import asyncio
# import uuid
# import zipfile
# from io import BytesIO
# from typing import Dict
# from services.compress import auto_compress

# class TaskStatus:
#     QUEUED = "queued"
#     PROCESSING = "processing"
#     DONE = "done"
#     ERROR = "error"

# class CompressionTask:
#     def __init__(self, files):
#         self.id = str(uuid.uuid4())
#         self.status = TaskStatus.QUEUED
#         self.progress = 0
#         self.error = None
#         self.files = files
#         self.results = {}
#         self.compressed_sizes = {}
#         self.total_files = len(files)
#         self.completed_files = 0
#         self.size_before = 0
#         self.file_progress = {}

#         for file_data in files:
#             self.file_progress[file_data["filename"]] = 0

# class CompressionQueue:
#     def __init__(self):
#         self.queue = asyncio.Queue()
#         self.tasks: Dict[str, CompressionTask] = {}
#         # KLUCZOWA ZMIANA: Limitujemy całkowitą liczbę procesów cjpeg/pngquant
#         # Na 2 rdzeniach optymalnie to 2-3 procesy naraz, reszta czeka w kolejce.
#         self.max_parallel_processes = asyncio.Semaphore(3)

#     async def add_task(self, files):
#         task = CompressionTask(files)
#         self.tasks[task.id] = task
#         # Obliczamy wagę zadania na starcie
#         task.size_before = sum(len(f["data"]) for f in files) / (1024 * 1024)
#         await self.queue.put(task)
#         return task.id

#     def get_task(self, task_id):
#         return self.tasks.get(task_id)

#     async def worker(self):
#         while True:
#             task = await self.queue.get()
#             task.status = TaskStatus.PROCESSING
#             try:
#                 # Przetwarzamy pliki z zadania, ale każdy plik musi dostać semafor
#                 await self.process_batch(task)
#                 if task.results:
#                     task.progress = 100
#                     task.status = TaskStatus.DONE
#                 else:
#                     task.status = TaskStatus.ERROR
#                     task.error = "All files failed"
#             except Exception as e:
#                 task.status = TaskStatus.ERROR
#                 task.error = str(e)
#             finally:
#                 self.queue.task_done()

#     async def process_batch(self, task):
#         # Używamy asyncio.gather, ale każde zadanie wewnątrz musi czekać na semafor procesora
#         jobs = [self.process_single_file_with_semaphore(task, f) for f in task.files]
#         await asyncio.gather(*jobs)

#     async def process_single_file_with_semaphore(self, task, file_data):
#         # Czekamy na wolny rdzeń procesora
#         async with self.max_parallel_processes:
#             filename = file_data["filename"]
#             data = file_data["data"]
#             try:
#                 # CPU-bound work
#                 compressed = await asyncio.to_thread(auto_compress, data, filename)
                
#                 task.results[filename] = compressed
#                 task.file_progress[filename] = 100
#                 task.compressed_sizes[filename] = len(compressed)
#                 task.completed_files += 1
#                 task.progress = int((task.completed_files / task.total_files) * 100)
#             except Exception as e:
#                 print(f"Error {filename}: {e}")

#     def build_zip(self, task):
#         zip_buffer = BytesIO()
#         with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
#             for filename, data in task.results.items():
#                 zipf.writestr(filename, data)
#         zip_buffer.seek(0)
#         return zip_buffer