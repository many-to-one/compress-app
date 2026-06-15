# # FILE: services/compress.py
# import asyncio
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
#         img = Image.open(BytesIO(input_bytes))
#         if img.mode != "RGB":
#             img = img.convert("RGB")

#     except Exception:
#         return input_bytes

#     ppm_buffer = BytesIO()

#     img.save(
#         ppm_buffer,
#         format="PPM"
#     )

#     ppm_data = ppm_buffer.getvalue()

#     cmd = [
#         "cjpeg",

#         "-quality", str(quality),

#         "-quant-table", "2",

#         "-optimize",

#         "-progressive",

#         "-dct", "float",

#         "-sample", "2x2"
#     ]

#     try:

#         process = subprocess.run(
#             cmd,
#             input=ppm_data,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             timeout=30
#         )

#         if process.returncode != 0:
#             print(process.stderr.decode())
#             return input_bytes

#         return process.stdout

#     except Exception as e:
#         print(e)
#         return input_bytes


# # async def compress_jpeg(
# #     input_bytes: bytes,
# #     quality: int = 75
# # ) -> bytes:

# #     return await asyncio.to_thread(
# #         _compress_jpeg_sync,
# #         input_bytes,
# #         quality
# #     )


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

#     # raise ValueError(
#     #     "Unsupported file format"
#     # )

#     return input_bytes


# ==========================================================================================================

import io
import subprocess
from PIL import Image
from io import BytesIO

def compress_png(input_bytes: bytes) -> bytes:
    # pngquant jest bardzo szybki, ale przy dużych plikach warto użyć --speed 4-5
    cmd = ["pngquant", "--quality", "65-80", "--speed", "4", "-"]
    try:
        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.communicate(input=input_bytes)
        return out if process.returncode == 0 else input_bytes
    except:
        return input_bytes

def compress_jpeg(input_bytes: bytes, quality: int = 75) -> bytes:
    try:
        # Optymalizacja RAM: Zamiast trzymać PPM w bytes, piszemy prosto do pipe'a
        img = Image.open(BytesIO(input_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        cmd = [
            "cjpeg", "-quality", str(quality), 
            "-optimize", "-progressive", "-dct", "float"
        ]
        
        process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        # Przekazujemy obraz w formacie PPM bezpośrednio do cjpeg
        # To oszczędza jedną kopię bytes w pamięci
        img.save(process.stdin, format="PPM")
        process.stdin.close()
        
        out = process.stdout.read()
        process.wait()
        
        return out if process.returncode == 0 else input_bytes
    except Exception as e:
        print(f"JPEG Error: {e}")
        return input_bytes

def auto_compress(input_bytes: bytes, filename: str) -> bytes:
    ext = filename.lower().split(".")[-1]
    # Jeśli plik jest bardzo duży, możemy tu dodać logikę agresywniejszej kompresji
    if ext in ["jpg", "jpeg"]:
        return compress_jpeg(input_bytes)
    elif ext == "png":
        return compress_png(input_bytes)
    elif ext == "webp":
        # Pillow dla webp jest całkiem wydajny
        img = Image.open(BytesIO(input_bytes))
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=80, method=4)
        return buf.getvalue()
    return input_bytes