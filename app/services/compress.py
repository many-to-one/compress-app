# # FILE: services/compress.py
# import io
# from io import BytesIO
# from PIL import Image
# import pillow_avif  # optional
# import pillow_heif  # optional

# import subprocess
# import tempfile

# def compress_png(input_bytes: bytes, min_quality: int = 65, max_quality: int = 80) -> bytes:
#     """
#     Kompresuje PNG używając pngquant (stratna kompresja wysokiej jakości).
#     Parametry quality określają dopuszczalny zakres utraty jakości.
#     """
#     # Flagi pngquant:
#     # --quality: zakres jakości (0-100)
#     # --speed: 1 (najwolniejsza/najlepsza) do 11 (najszybsza)
#     # - (oznacza czytanie z stdin i pisanie na stdout)
#     cmd = [
#         "pngquant",
#         "--quality", f"{min_quality}-{max_quality}",
#         "--speed", "3",
#         "-"
#     ]

#     try:
#         process = subprocess.Popen(
#             cmd,
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )

#         output, stderr = process.communicate(input=input_bytes)

#         # pngquant zwraca 99, jeśli nie udało się utrzymać min_quality
#         if process.returncode == 0:
#             return output
#         elif process.returncode == 99:
#             # Jeśli jakość była zbyt niska, spróbuj z szerszym zakresem lub zwróć oryginał
#             print("pngquant: nie udało się utrzymać zadanej jakości, zwracam oryginał.")
#             return input_bytes
#         else:
#             print(f"Błąd pngquant: {stderr.decode()}")
#             return input_bytes

#     except Exception as e:
#         print(f"Wyjątek podczas kompresji PNG: {e}")
#         return input_bytes



# # === mozjpeg ===


# # def compress_jpeg(input_bytes: bytes, quality: int = 75) -> bytes:
# #     try:
# #         img = Image.open(BytesIO(input_bytes))
# #         img = img.convert("RGB")
# #         # print("===compress_jpeg===", img)
# #     except Exception as e:
# #         print("Błąd otwierania obrazu:", e)
# #         return input_bytes

# #     ppm_buffer = BytesIO()
# #     img.save(ppm_buffer, format="PPM")
# #     ppm_data = ppm_buffer.getvalue()
# #     # print("===ppm_data===", ppm_data)

# #     cmd = [
# #         "cjpeg",
# #         "-quality", str(quality),          # Zmniejszenie z 85 na 75 (często złoty środek)
# #         "-quant-table", "2",       # Najlepsze tablice dla MozJPEG
# #         "-optimize",               # Optymalizacja (jeśli nie używasz -arithmetic)
# #         "-progressive",            # Progresywne wyświetlanie
# #         "-dct", "float",           # Najdokładniejsza metoda obliczeń
# #         "-sample", "2x2"           # Subsampling 4:2:0 (oszczędność na kolorach niewidoczna dla oka)
# #     ]

# #     try:
# #         process = subprocess.Popen(
# #             cmd,
# #             stdin=subprocess.PIPE,
# #             stdout=subprocess.PIPE,
# #             stderr=subprocess.PIPE
# #         )
# #         output, stderr = process.communicate(ppm_data)

# #         if process.returncode != 0:
# #             print("Błąd cjpeg:", stderr.decode())
# #             return input_bytes  # fallback

# #         # print("===OUTPUT===", output)
# #         return output

# #     except Exception as e:
# #         print("Wyjątek w cjpeg:", e)
# #         return input_bytes




# def compress_webp(input_bytes: bytes) -> bytes:
#     img = Image.open(BytesIO(input_bytes))

#     buffer = BytesIO()
#     img.save(
#         buffer,
#         format="WEBP",
#         quality=90,
#         method=6
#     )
#     return buffer.getvalue()


# # def auto_compress(input_bytes: bytes, filename: str) -> bytes:
# #     ext = filename.lower().split(".")[-1]

# #     print("===auto_compress===", ext)

# #     if ext in ["png"]:
# #         return compress_png(input_bytes)
# #     elif ext in ["jpg", "jpeg"]:
# #         return compress_jpeg(input_bytes)
# #     elif ext in ["webp"]:
# #         return compress_webp(input_bytes)
# #     else:
# #         raise ValueError("Unsupported file format")


# def auto_convert_to_webp(data: bytes, filename: str) -> bytes:
#     img = Image.open(io.BytesIO(data))

#     output = io.BytesIO()
#     img.save(output, format="WEBP", quality=85)

#     return output.getvalue()




# from PIL import Image

# from io import BytesIO

# import subprocess
# import tempfile
# import os

# # =========================
# # JPEG
# # =========================

# def compress_jpeg(
#     input_bytes: bytes,
#     quality: int = 75
# ) -> bytes:

#     try:

#         img = Image.open(
#             BytesIO(input_bytes)
#         )

#         img = img.convert("RGB")

#     except Exception as e:

#         print("Image open error:", e)

#         return input_bytes

#     with tempfile.NamedTemporaryFile(
#         suffix=".jpg",
#         delete=False
#     ) as input_file, tempfile.NamedTemporaryFile(
#         suffix=".jpg",
#         delete=False
#     ) as output_file:

#         try:

#             img.save(
#                 input_file,
#                 format="JPEG",
#                 quality=100
#             )

#             input_file.flush()

#             cmd = [
#                 "cjpeg",

#                 "-quality",
#                 str(quality),

#                 "-quant-table",
#                 "2",

#                 "-optimize",

#                 "-progressive",

#                 "-sample",
#                 "2x2",

#                 "-outfile",
#                 output_file.name,

#                 input_file.name
#             ]

#             result = subprocess.run(
#                 cmd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE
#             )

#             if result.returncode != 0:

#                 print(
#                     "mozjpeg error:",
#                     result.stderr.decode()
#                 )

#                 return input_bytes

#             with open(
#                 output_file.name,
#                 "rb"
#             ) as f:

#                 compressed = f.read()

#             return compressed

#         except Exception as e:

#             print("compress_jpeg:", e)

#             return input_bytes

#         finally:

#             try:
#                 os.unlink(input_file.name)
#             except:
#                 pass

#             try:
#                 os.unlink(output_file.name)
#             except:
#                 pass

# # =========================
# # AUTO
# # =========================

# def auto_compress(
#     input_bytes: bytes,
#     filename: str
# ) -> bytes:

#     ext = filename.lower().split(".")[-1]

#     if ext in ["jpg", "jpeg"]:

#         return compress_jpeg(
#             input_bytes
#         )

#     elif ext == "png":

#         return compress_png(
#             input_bytes
#         )

#     elif ext == "webp":

#         return compress_webp(
#             input_bytes
#         )

#     raise ValueError(
#         "Unsupported file format"
#     )





# =======================================================================================
# **************************************************************************************
# ======================================================================================

# FILE: services/compress.py
import asyncio
import io
from io import BytesIO
from PIL import Image
import pillow_avif  # optional
import pillow_heif  # optional

import subprocess
import tempfile

def compress_png(input_bytes: bytes, min_quality: int = 65, max_quality: int = 80) -> bytes:
    """
    Kompresuje PNG używając pngquant (stratna kompresja wysokiej jakości).
    Parametry quality określają dopuszczalny zakres utraty jakości.
    """
    # Flagi pngquant:
    # --quality: zakres jakości (0-100)
    # --speed: 1 (najwolniejsza/najlepsza) do 11 (najszybsza)
    # - (oznacza czytanie z stdin i pisanie na stdout)
    cmd = [
        "pngquant",
        "--quality", f"{min_quality}-{max_quality}",
        "--speed", "3",
        "-"
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output, stderr = process.communicate(input=input_bytes)

        # pngquant zwraca 99, jeśli nie udało się utrzymać min_quality
        if process.returncode == 0:
            return output
        elif process.returncode == 99:
            # Jeśli jakość była zbyt niska, spróbuj z szerszym zakresem lub zwróć oryginał
            print("pngquant: nie udało się utrzymać zadanej jakości, zwracam oryginał.")
            return input_bytes
        else:
            print(f"Błąd pngquant: {stderr.decode()}")
            return input_bytes

    except Exception as e:
        print(f"Wyjątek podczas kompresji PNG: {e}")
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





def auto_convert_to_webp(data: bytes, filename: str) -> bytes:
    img = Image.open(io.BytesIO(data))

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=85)

    return output.getvalue()




from PIL import Image

from io import BytesIO

import subprocess
import tempfile
import os

# =========================
# JPEG
# =========================

def compress_jpeg(
    input_bytes: bytes,
    quality: int = 75
) -> bytes:

    try:
        img = Image.open(BytesIO(input_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

    except Exception:
        return input_bytes

    ppm_buffer = BytesIO()

    img.save(
        ppm_buffer,
        format="PPM"
    )

    ppm_data = ppm_buffer.getvalue()

    cmd = [
        "cjpeg",

        "-quality", str(quality),

        "-quant-table", "2",

        "-optimize",

        "-progressive",

        "-dct", "float",

        "-sample", "2x2"
    ]

    try:

        process = subprocess.run(
            cmd,
            input=ppm_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        if process.returncode != 0:
            print(process.stderr.decode())
            return input_bytes

        return process.stdout

    except Exception as e:
        print(e)
        return input_bytes


# async def compress_jpeg(
#     input_bytes: bytes,
#     quality: int = 75
# ) -> bytes:

#     return await asyncio.to_thread(
#         _compress_jpeg_sync,
#         input_bytes,
#         quality
#     )


# =========================
# AUTO
# =========================

def auto_compress(
    input_bytes: bytes,
    filename: str
) -> bytes:

    ext = filename.lower().split(".")[-1]

    if ext in ["jpg", "jpeg"]:

        return compress_jpeg(
            input_bytes
        )

    elif ext == "png":

        return compress_png(
            input_bytes
        )

    elif ext == "webp":

        return compress_webp(
            input_bytes
        )

    # raise ValueError(
    #     "Unsupported file format"
    # )

    return input_bytes