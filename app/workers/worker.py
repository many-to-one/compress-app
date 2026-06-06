import subprocess
import os

def compress_video(input_path, output_path, crf=26):
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vcodec", "libx265",
        "-crf", str(crf),
        "-preset", "medium",
        "-acodec", "aac",
        "-b:a", "128k",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    before = os.path.getsize(input_path)
    after = os.path.getsize(output_path)

    return {
        "before_mb": round(before / 1024 / 1024, 2),
        "after_mb": round(after / 1024 / 1024, 2),
        "output_path": output_path
    }
