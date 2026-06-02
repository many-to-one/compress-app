# from fastapi import APIRouter
# from fastapi import UploadFile
# from fastapi import HTTPException
# from fastapi import Depends

# from fastapi.responses import StreamingResponse

# from io import BytesIO

# import zipfile
# import requests
# import json


# from services.queue import TaskStatus
# # from services.queue_manager import compression_queue
# import services.queue_manager as queue_manager



# router = APIRouter()

# # =========================
# # SINGLE FILE TASK
# # =========================

# @router.post("/batch")
# async def compress_batch(file: UploadFile):

#     if not file:
#         raise HTTPException(400, "No file")

#     content = await file.read()

#     task_id = await queue_manager.compression_queue.add_task(
#     # task_id = await compression_queue.add_task(
#         [(file.filename, content)]
#     )

#     return {
#         "task_id": task_id
#     }

# # =========================
# # STATUS
# # =========================

# @router.get("/status/{task_id}")
# async def get_task_status(task_id: str):

#     task = queue_manager.compression_queue.get_task(task_id)
#     # task = compression_queue.get_task(task_id)

#     if not task:
#         raise HTTPException(404, "Task not found")

#     compressed_size = 0

#     if task.compressed_sizes:
#         compressed_size = sum(
#             task.compressed_sizes.values()
#         )

#     return {
#         "status": task.status,
#         "progress": task.progress,
#         "compressed_size": compressed_size
#     }

# # =========================
# # DOWNLOAD SINGLE
# # =========================

# @router.get("/file/{task_id}")
# async def download_single_file(task_id: str):

#     task = queue_manager.compression_queue.get_task(task_id)
#     # task = queue_manager.compression_queue.get_task(task_id)

#     if not task:
#         raise HTTPException(404, "Task not found")

#     if task.status != TaskStatus.DONE:
#         raise HTTPException(400, "Task not finished")

#     if not task.results:
#         raise HTTPException(400, "No results")

#     filename = list(task.results.keys())[0]

#     data = task.results[filename]

#     return StreamingResponse(
#         BytesIO(data),
#         media_type="application/octet-stream",
#         headers={
#             "Content-Disposition":
#             f'attachment; filename="{filename}"'
#         }
#     )

# # =========================
# # DOWNLOAD ZIP
# # =========================

# @router.get("/download-multi")
# async def download_multiple_files(tasks: str):

#     task_ids = tasks.split(",")

#     zip_buffer = BytesIO()

#     with zipfile.ZipFile(
#         zip_buffer,
#         "w",
#         zipfile.ZIP_DEFLATED
#     ) as zf:

#         for task_id in task_ids:

#             task = queue_manager.compression_queue.get_task(task_id)

#             if not task:
#                 continue

#             if task.status != TaskStatus.DONE:
#                 continue

#             for filename, data in task.results.items():

#                 zf.writestr(
#                     filename,
#                     data
#                 )

#     zip_buffer.seek(0)

#     return StreamingResponse(
#         zip_buffer,
#         media_type="application/zip",
#         headers={
#             "Content-Disposition":
#             'attachment; filename="compressed_images.zip"'
#         }
#     )


# def download_from_drive(access_token, file_id):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
#     r = requests.get(url, headers=headers)
#     return r.content


# def upload_to_drive(access_token, folder_id, filename, file_bytes):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     metadata = {"name": filename, "parents": [folder_id]}

#     files = {
#         "metadata": ("metadata", json.dumps(metadata), "application/json"),
#         "file": (filename, file_bytes)
#     }

#     r = requests.post(
#         "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
#         headers=headers,
#         files=files
#     )
#     return r.json()












from io import BytesIO

from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException

from fastapi.responses import StreamingResponse

import services.queue_manager as queue_manager


router = APIRouter()


# =========================
# CREATE TASK
# =========================

@router.post("/compress/batch")
async def compress_batch(
    files: list[UploadFile] = File(...)
):

    compression_queue = queue_manager.compression_queue

    if compression_queue is None:
        raise HTTPException(500, "Queue not initialized")

    prepared_files = []

    for file in files:

        prepared_files.append({
            "filename": file.filename,
            "data": await file.read()
        })

    task_id = await compression_queue.add_task(
        prepared_files
    )

    print(f"===============Added task {task_id} to the queue")

    return {
        "task_id": task_id
    }


# =========================
# STATUS
# =========================

@router.get("/compress/status/{task_id}")
async def get_status(task_id: str):

    compression_queue = queue_manager.compression_queue

    task = compression_queue.get_task(task_id)

    if not task:
        raise HTTPException(404)

    return {
        "status": task.status,
        "progress": task.progress,
        "files": task.file_progress
    }


# =========================
# DOWNLOAD FILE
# =========================

@router.get("/compress/download/{task_id}/{filename}")
async def download_file(
    task_id: str,
    filename: str
):

    compression_queue = queue_manager.compression_queue

    task = compression_queue.get_task(task_id)

    if not task:
        raise HTTPException(404)

    if filename not in task.results:
        raise HTTPException(404)

    return StreamingResponse(
        BytesIO(task.results[filename]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition":
            f'attachment; filename="{filename}"'
        }
    )


# =========================
# DOWNLOAD ZIP
# =========================

@router.get("/compress/download-zip/{task_id}")
async def download_zip(task_id: str):

    compression_queue = queue_manager.compression_queue

    task = compression_queue.get_task(task_id)

    if not task:
        raise HTTPException(404)

    if task.status != "done":
        raise HTTPException(400)

    zip_buffer = compression_queue.build_zip(task)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
            'attachment; filename="compressed.zip"'
        }
    )