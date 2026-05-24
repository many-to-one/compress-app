# FILE: services/compress.py
import io
from io import BytesIO
from PIL import Image
import pillow_avif  # optional
import pillow_heif  # optional

def compress_png(input_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(input_bytes)).convert("RGBA")

    buffer = BytesIO()
    img.save(
        buffer,
        format="PNG",
        optimize=True,
        compress_level=9
    )
    return buffer.getvalue()


def compress_jpg(input_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(input_bytes)).convert("RGB")

    buffer = BytesIO()
    img.save(
        buffer,
        format="JPEG",
        quality=90,
        optimize=True,
        progressive=True,
        subsampling=2
    )
    return buffer.getvalue()


def compress_webp(input_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(input_bytes))

    buffer = BytesIO()
    img.save(
        buffer,
        format="WEBP",
        quality=90,
        method=6
    )
    return buffer.getvalue()


def auto_compress(input_bytes: bytes, filename: str) -> bytes:
    ext = filename.lower().split(".")[-1]

    if ext in ["png"]:
        return compress_png(input_bytes)
    elif ext in ["jpg", "jpeg"]:
        return compress_jpg(input_bytes)
    elif ext in ["webp"]:
        return compress_webp(input_bytes)
    else:
        raise ValueError("Unsupported file format")


def auto_convert_to_webp(data: bytes, filename: str) -> bytes:
    img = Image.open(io.BytesIO(data))

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85)

    return output.getvalue()