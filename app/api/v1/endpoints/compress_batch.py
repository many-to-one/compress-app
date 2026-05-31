# from fastapi import APIRouter, UploadFile, HTTPException
# from fastapi.responses import StreamingResponse, FileResponse
# from services.queue import compression_queue, TaskStatus
# from io import BytesIO
# import zipfile

# router = APIRouter()

# @router.post("/batch")
# async def compress_batch(files: list[UploadFile]):
#     if not files:
#         raise HTTPException(400, "No files provided")
    
#     # Przyjmujemy listę, ale JS wysyła teraz po jednym dla asynchroniczności
#     file_data = []
#     for f in files:
#         content = await f.read()
#         file_data.append((f.filename, content))

#     task_id = await compression_queue.add_task(file_data)
#     return {"task_id": task_id}

# @router.get("/status/{task_id}")
# async def get_task_status(task_id: str):
#     task = compression_queue.get_task(task_id)
#     if not task:
#         raise HTTPException(404, "Task not found")

#     return {
#         "status": task.status,
#         "progress": task.progress,
#         "file_progress": task.file_progress,
#         "compressed_sizes": task.compressed_sizes,
#         "name_map": task.name_map,
#     }

# # Pobieranie pojedynczego pliku
# @router.get("/file/{task_id}")
# async def download_single_file(task_id: str):
#     task = compression_queue.get_task(task_id)
#     if not task or task.status != TaskStatus.DONE:
#         raise HTTPException(404, "File not ready or task not found")

#     # Pobieramy pierwszy (i w tym przypadku jedyny) wynik z zadania
#     filename = list(task.results.keys())[0]
#     file_bytes = task.results[filename]
    
#     return StreamingResponse(
#         BytesIO(file_bytes),
#         media_type="application/octet-stream",
#         headers={"Content-Disposition": f"attachment; filename={filename}"}
#     )

# # Pobieranie ZIP (dla wstecznej kompatybilności lub zadań wieloplikowych)
# @router.get("/download/{task_id}")
# async def download_zip(task_id: str):
#     task = compression_queue.get_task(task_id)
#     if not task or task.status != TaskStatus.DONE:
#         raise HTTPException(400, "Task not finished")

#     zip_buffer = BytesIO()
#     with zipfile.ZipFile(zip_buffer, "w") as zf:
#         for filename, content in task.results.items():
#             zf.writestr(filename, content)
    
#     zip_buffer.seek(0)
#     return StreamingResponse(
#         zip_buffer,
#         media_type="application/zip",
#         headers={"Content-Disposition": f"attachment; filename=compressed_{task_id}.zip"}
#     )





from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import HTTPException
from fastapi import Depends

from fastapi.responses import StreamingResponse

from io import BytesIO

import zipfile

from services.queue import compression_queue
from services.queue import TaskStatus

router = APIRouter()

# =========================
# SINGLE FILE TASK
# =========================

@router.post("/batch")
async def compress_batch(file: UploadFile):

    if not file:
        raise HTTPException(400, "No file")

    content = await file.read()

    task_id = await compression_queue.add_task(
        [(file.filename, content)]
    )

    return {
        "task_id": task_id
    }

# =========================
# STATUS
# =========================

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):

    task = compression_queue.get_task(task_id)

    if not task:
        raise HTTPException(404, "Task not found")

    compressed_size = 0

    if task.compressed_sizes:
        compressed_size = sum(
            task.compressed_sizes.values()
        )

    return {
        "status": task.status,
        "progress": task.progress,
        "compressed_size": compressed_size
    }

# =========================
# DOWNLOAD SINGLE
# =========================

@router.get("/file/{task_id}")
async def download_single_file(task_id: str):

    task = compression_queue.get_task(task_id)

    if not task:
        raise HTTPException(404, "Task not found")

    if task.status != TaskStatus.DONE:
        raise HTTPException(400, "Task not finished")

    if not task.results:
        raise HTTPException(400, "No results")

    filename = list(task.results.keys())[0]

    data = task.results[filename]

    return StreamingResponse(
        BytesIO(data),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition":
            f'attachment; filename="{filename}"'
        }
    )

# =========================
# DOWNLOAD ZIP
# =========================

@router.get("/download-multi")
async def download_multiple_files(tasks: str):

    task_ids = tasks.split(",")

    zip_buffer = BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zf:

        for task_id in task_ids:

            task = compression_queue.get_task(task_id)

            if not task:
                continue

            if task.status != TaskStatus.DONE:
                continue

            for filename, data in task.results.items():

                zf.writestr(
                    filename,
                    data
                )

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
            'attachment; filename="compressed_images.zip"'
        }
    )
