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
        return self.tasks.get(task_id)

    # =====================
    # WORKER
    # =====================

    async def worker(self):

        while True:
            task = await self.queue.get()

            task.status = VideoStatus.PROCESSING

            try:
                await self.process_video(task)
                task.status = VideoStatus.DONE
                task.progress = 100

            except Exception as e:
                task.status = VideoStatus.ERROR
                task.error = str(e)

            finally:
                self.queue.task_done()

    # =====================
    # PROCESS VIDEO
    # =====================

    async def process_video(self, task: VideoTask):

        filename = task.file_data["filename"]
        data = task.file_data["data"]

        # 1) Sprawdzamy długość filmu
        task.progress = 5
        await asyncio.sleep(0)

        duration = await asyncio.to_thread(self.get_video_duration, data)
        if duration > 300:
            raise Exception("Film jest dłuższy niż 5 minut.")

        # 2) Kompresja z prawdziwym progresem
        task.progress = 10
        await asyncio.sleep(0)

        compressed = await self.compress_video_with_progress(task, data, duration)

        # 3) Zakończone
        task.result = compressed
        task.compressed_size = len(compressed)
        task.progress = 100


    # =====================
    # FFmpeg — długość filmu
    # =====================

    def get_video_duration(self, data: bytes) -> float:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")

            with open(input_path, "wb") as f:
                f.write(data)

            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return float(result.stdout.decode().strip())

    # =====================
    # FFmpeg — kompresja
    # =====================

    async def compress_video_with_progress(
        self,
        task: VideoTask,
        data: bytes,
        duration: float,
        crf: int = 28
    ) -> bytes:

        with tempfile.TemporaryDirectory() as tmpdir:

            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, "output.mp4")

            # =========================
            # SAVE INPUT
            # =========================

            with open(input_path, "wb") as f:
                f.write(data)

            # =========================
            # FFMPEG
            # =========================

            cmd = [
                "ffmpeg",

                "-hide_banner",

                "-i", input_path,

                # VIDEO
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "30",
                # "-c:v", "libx264",
                # "-preset", "veryfast",
                # "-crf", str(crf),

                # AUDIO
                "-c:a", "aac",
                "-b:a", "96k",

                # WEB STREAMING
                "-movflags", "+faststart",

                # PROGRESS
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

                    await asyncio.sleep(0)

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

                return result

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
