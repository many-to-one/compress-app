import asyncio
import uuid
import tempfile
import subprocess
import os
import re
from typing import Dict


# =========================
# STATUS
# =========================

class VideoStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


# =========================
# TASK
# =========================

class VideoTask:

    def __init__(self, file_data):

        self.id = str(uuid.uuid4())

        self.status = VideoStatus.QUEUED
        self.progress = 0
        self.error = None

        self.file_data = file_data  # {"filename": ..., "data": ...}
        self.result = None
        self.compressed_size = 0


# =========================
# QUEUE
# =========================

FFMPEG_TIME_REGEX = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")

class VideoQueue:

    def __init__(self):
        self.queue = asyncio.Queue()
        self.tasks: Dict[str, VideoTask] = {}

    # =====================
    # ADD TASK
    # =====================

    async def add_task(self, file_data):

        task = VideoTask(file_data)
        self.tasks[task.id] = task

        await self.queue.put(task)

        return task.id

    # =====================
    # GET TASK
    # =====================

    def get_task(self, task_id):
        print("===get_task===", self.tasks)
        return self.tasks.get(task_id)

    # =====================
    # WORKER
    # =====================

    async def worker(self):
        # Aby umożliwić kompresję 3 filmów na raz, możemy użyć Semaphore
        sem = asyncio.Semaphore(3) 

        async def run_task(task):
            async with sem:
                task.status = VideoStatus.PROCESSING
                try:
                    await self.process_video(task)
                    task.status = VideoStatus.DONE
                except Exception as e:
                    task.status = VideoStatus.ERROR
                    task.error = str(e)
                finally:
                    self.queue.task_done()

        while True:
            task = await self.queue.get()
            asyncio.create_task(run_task(task)) # Uruchamia zadania równolegle (do limitu semafora)



    # =====================
    # PROCESS VIDEO
    # =====================

    async def process_video(self, task: VideoTask):

        filename = task.file_data["filename"]
        filepath = task.file_data["filepath"]

        # =====================
        # CHECK DURATION
        # =====================

        task.progress = 5

        duration = await asyncio.to_thread(
            self.get_video_duration,
            filepath
        )

        if duration > 300:
            raise Exception("Film jest dłuższy niż 5 minut.")

        # =====================
        # COMPRESS
        # =====================

        task.progress = 10

        compressed = await self.compress_video_with_progress(
            task,
            filepath,
            duration
        )

        # =====================
        # DONE
        # =====================

        task.result = compressed
        task.compressed_size = len(compressed)

        try:
            original_size = os.path.getsize(filepath)
        except:
            original_size = 0

        print(
            f"Compressed {filename}: "
            f"{original_size} -> {len(compressed)} bytes"
        )

        task.progress = 100

        # =====================
        # CLEANUP
        # =====================

        try:
            os.remove(filepath)
        except:
            pass

    # async def process_video(self, task: VideoTask):

    #     filename = task.file_data["filename"]
    #     data = task.file_data["data"]

    #     # 1) Sprawdzamy długość filmu
    #     task.progress = 5
    #     # await asyncio.sleep(0)

    #     duration = await asyncio.to_thread(self.get_video_duration, data)
    #     if duration > 300:
    #         raise Exception("Film jest dłuższy niż 5 minut.")

    #     # 2) Kompresja z prawdziwym progresem
    #     task.progress = 10
    #     # await asyncio.sleep(0)

    #     compressed = await self.compress_video_with_progress(task, data, duration)

    #     # 3) Zakończone
    #     task.result = compressed
    #     task.compressed_size = len(compressed)
    #     print(f"==============Compressed {filename}: {len(data)} -> {len(compressed)} bytes")
    #     task.progress = 100


    # =====================
    # FFmpeg — długość filmu
    # =====================

    def get_video_duration(self, filepath: str) -> float:

        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            raise Exception(
                result.stderr.decode(errors="ignore")
            )

        return float(
            result.stdout.decode().strip()
        )

    # def get_video_duration(self, data: bytes) -> float:
    #     with tempfile.TemporaryDirectory() as tmpdir:
    #         input_path = os.path.join(tmpdir, "input.mp4")

    #         with open(input_path, "wb") as f:
    #             f.write(data)

    #         cmd = [
    #             "ffprobe",
    #             "-v", "error",
    #             "-show_entries", "format=duration",
    #             "-of", "default=noprint_wrappers=1:nokey=1",
    #             input_path
    #         ]

    #         result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         return float(result.stdout.decode().strip())

    # =====================
    # FFmpeg — kompresja
    # =====================

    async def compress_video_with_progress(
        self,
        task: VideoTask,
        # data: bytes,
        input_path: str,
        duration: float,
        crf: int = 28
    ) -> bytes:

        output_path = f"/tmp/output_{uuid.uuid4()}.mp4"

        # with tempfile.TemporaryDirectory() as tmpdir:

        #     input_path = os.path.join(tmpdir, "input.mp4")
            # output_path = os.path.join(tmpdir, "output.mp4")

        #     # =========================
        #     # SAVE INPUT
        #     # =========================

        #     with open(input_path, "wb") as f:
        #         f.write(data)

            # =========================
            # FFMPEG
            # =========================

            # cmd = [
            #     "ffmpeg",
            #     "-threads", "1",
            #     "-fflags", "+genpts",
            #     "-analyzeduration", "100M",
            #     "-probesize", "100M",

            #     "-hide_banner",

            #     "-i", input_path,

            #     # VIDEO
            #     "-c:v", "libx264",
            #     "-preset", "ultrafast",
            #     "-crf", "30",
            #     # "-c:v", "libx264",
            #     # "-preset", "veryfast",
            #     # "-crf", str(crf),

            #     # AUDIO
            #     "-c:a", "aac",
            #     "-b:a", "96k",

            #     # WEB STREAMING
            #     "-movflags", "+faststart",

            #     # PROGRESS
            #     "-progress", "pipe:1",
            #     "-nostats",

            #     output_path,
            #     "-y"
            # ]

        cmd = [
            "ffmpeg",

            "-threads", "1",

            "-fflags", "+genpts",

            "-analyzeduration", "20M",
            "-probesize", "20M",

            "-hide_banner",

            "-i", input_path,

            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", str(crf),

            "-c:a", "aac",
            "-b:a", "96k",

            "-movflags", "+faststart",

            "-progress", "pipe:1",
            "-nostats",

            output_path,
            "-y"
        ]

        print("START FFMPEG")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:

            while True:

                line = await process.stdout.readline()

                if not line:
                    break

                line = line.decode("utf-8").strip()

                # DEBUG
                # print("FFMPEG:", line)

                if line.startswith("out_time_ms="):

                    try:

                        micros = int(
                            line.split("=")[1]
                        )

                        current_seconds = micros / 1_000_000

                        progress = int(
                            (current_seconds / duration) * 100
                        )

                        progress = max(0, min(progress, 99))

                        task.progress = max(
                            task.progress,
                            progress
                        )

                    except Exception:
                        pass

                # await asyncio.sleep(0)

            # =========================
            # WAIT PROCESS
            # =========================

            try:

                await asyncio.wait_for(
                    process.wait(),
                    timeout=180
                )

            except asyncio.TimeoutError:

                process.kill()

                raise Exception(
                    "Kompresja przekroczyła limit czasu (180s)"
                )

            print("END FFMPEG")

            # =========================
            # ERROR CHECK
            # =========================

            if process.returncode != 0:

                stderr = await process.stderr.read()

                raise Exception(
                    f"FFmpeg error:\n{stderr.decode(errors='ignore')}"
                )

            if not os.path.exists(output_path):

                raise Exception(
                    "FFmpeg nie wygenerował pliku wynikowego."
                )

            # =========================
            # LOAD OUTPUT
            # =========================

            with open(output_path, "rb") as f:
                result = f.read()

            try:
                os.remove(output_path)
            except:
                pass

            return result

            # with open(output_path, "rb") as f:
            #     result = f.read()

            # return result

        finally:

            if process.returncode is None:
                process.kill()


    # =====================
    # POZYCJA W KOLEJCE
    # =====================

    def get_position(self, task_id):
        task = self.tasks.get(task_id)
        if not task:
            return None

        if task.status != VideoStatus.QUEUED:
            return 0

        queued_tasks = [t for t in self.tasks.values() if t.status == VideoStatus.QUEUED]

        return queued_tasks.index(task)
