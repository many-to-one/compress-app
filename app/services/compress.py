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


# def compress_jpg(input_bytes: bytes) -> bytes:
#     img = Image.open(BytesIO(input_bytes)).convert("RGB")
#     img = img.convert("RGB")

#     buffer = BytesIO()
#     img.save(
#         buffer,
#         format="JPEG",
#         quality=90,
#         optimize=True,
#         progressive=True,
#         subsampling=2
#     )
#     return buffer.getvalue()

# def compress_jpg(input_bytes: bytes) -> bytes:
#     img = Image.open(BytesIO(input_bytes))
#     icc = img.info.get("icc_profile")

#     # usuń EXIF
#     img_no_exif = Image.new(img.mode, img.size)
#     img_no_exif.putdata(list(img.getdata()))
#     img = img_no_exif.convert("RGB")

#     buffer = BytesIO()
#     img.save(
#         buffer,
#         format="JPEG",
#         quality=85,
#         optimize=True,
#         progressive=True,
#         subsampling=1,   # 4:2:2
#         icc_profile=icc
#     )
#     return buffer.getvalue()



# === mozjpeg ===
# import subprocess

# def compress_jpeg(input_bytes: bytes, quality: int = 85) -> bytes:
#     # 1. Wczytaj obraz i upewnij się, że jest w RGB
#     try:
#         img = Image.open(BytesIO(input_bytes))
#         if img.mode != "RGB":
#             img = img.convert("RGB")
#     except Exception as e:
#         print(f"Błąd otwierania obrazu: {e}")
#         return input_bytes

#     # 2. Zapisz do PPM (najszybszy format pośredni dla cjpeg)
#     ppm_buffer = BytesIO()
#     img.save(ppm_buffer, format="PPM")
#     ppm_data = ppm_buffer.getvalue()

#     # 3. Uruchom mozjpeg (cjpeg)
#     # Wyjaśnienie flag:
#     # -quality: jakość 0-100
#     # -optimize: optymalizacja tablic Huffmana
#     # -progressive: tworzy progresywny JPEG (lepszy do sieci)
#     # -dct float: najdokładniejsza metoda liczenia DCT
#     cmd = [
#         "cjpeg",
#         "-quality", str(quality),
#         "-optimize",
#         "-progressive",
#         "-dct", "float", 
#         "-sample", "2x2" 
#     ]

#     process = subprocess.Popen(
#         cmd,
#         stdin=subprocess.PIPE,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE  # Przechwytujemy błędy
#     )

#     output, stderr = process.communicate(ppm_data)

#     if process.returncode != 0:
#         print(f"Błąd cjpeg: {stderr.decode()}")
#         # W razie błędu zwróć oryginał lub rzuć wyjątek
#         return input_bytes

#     return output

def compress_jpeg(input_bytes: bytes, quality: int = 85) -> bytes:
    try:
        img = Image.open(BytesIO(input_bytes))
        img = img.convert("RGB")
        print("===compress_jpeg===", img)
    except Exception as e:
        print("Błąd otwierania obrazu:", e)
        return input_bytes

    ppm_buffer = BytesIO()
    img.save(ppm_buffer, format="PPM")
    ppm_data = ppm_buffer.getvalue()
    print("===ppm_data===", ppm_data)

    cmd = [
        "cjpeg",
        "-quality", str(quality),
        "-optimize",
        "-progressive",
        "-dct", "float",
        "-sample", "2x2"
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, stderr = process.communicate(ppm_data)

        if process.returncode != 0:
            print("Błąd cjpeg:", stderr.decode())
            return input_bytes  # fallback

        print("===OUTPUT===", output)
        return output

    except Exception as e:
        print("Wyjątek w cjpeg:", e)
        return input_bytes




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

    print("===auto_compress===", ext)

    if ext in ["png"]:
        return compress_png(input_bytes)
    elif ext in ["jpg", "jpeg"]:
        return compress_jpeg(input_bytes)
    elif ext in ["webp"]:
        return compress_webp(input_bytes)
    else:
        raise ValueError("Unsupported file format")


def auto_convert_to_webp(data: bytes, filename: str) -> bytes:
    img = Image.open(io.BytesIO(data))

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85)

    return output.getvalue()