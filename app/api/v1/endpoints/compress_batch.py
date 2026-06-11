from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
import services.queue_manager as queue_manager
import services.video_queue_manager as video_queue_manager
from starlette.responses import JSONResponse, Response
from starlette.background import BackgroundTasks
from typing import List, Dict
import asyncio
import uuid
from services.queue import TaskStatus
import zipfile
import urllib
import requests
import json

from core.config import settings
from crud.user import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db


router = APIRouter()

# =========================
# KOMPRESJA (Dostosowane do JS: klucz "file")
# =========================
@router.post("/batch")
async def compress_batch(
    file: UploadFile = File(...)  # Zmieniono z files: list na file: UploadFile
):
    q = queue_manager.compression_queue
    if q is None:
        raise HTTPException(500, "Queue not initialized")

    # Przygotowujemy listę z jednym plikiem (kolejka i tak przyjmuje listę)
    content = await file.read()
    prepared_files = [{
        "filename": file.filename,
        "data": content
    }]

    task_id = await q.add_task(prepared_files)
    return {"task_id": task_id}


# =========================
# WEBP (Dodaj, jeśli używasz w JS)
# =========================
@router.post("/batch-webp")
async def compress_batch_webp(
    file: UploadFile = File(...)
):
    q = queue_manager.compression_queue
    if q is None:
        raise HTTPException(500, "Queue not initialized")

    content = await file.read()
    prepared_files = [{
        "filename": file.filename,
        "data": content
    }]

    # Tutaj możesz dodać mode="webp" jeśli Twoja kolejka to obsługuje
    task_id = await q.add_task(prepared_files) 
    return {"task_id": task_id}



# =========================
# STATUS
# =========================
@router.get("/status/{task_id}")
async def get_status(task_id: str):
    q = queue_manager.compression_queue
    task = q.get_task(task_id)

    if not task:
        raise HTTPException(404, "Task not found")

    # Obliczamy rozmiar skompresowany dla UI
    c_size = sum(task.compressed_sizes.values()) if task.compressed_sizes else 0

    return {
        "status": task.status,
        "progress": task.progress,
        "compressed_size": c_size,
        "files": task.file_progress
    }


# =========================
# DOWNLOAD FILE
# =========================
@router.get("/file/{task_id}")
async def download_file(task_id: str):
    q = queue_manager.compression_queue
    task = q.get_task(task_id)

    if not task or not task.results:
        raise HTTPException(404, "File not ready")

    # Pobieramy pierwszy dostępny wynik
    filename = list(task.results.keys())[0]
    data = task.results[filename]

    return StreamingResponse(
        BytesIO(data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/download-zip/{task_id}")
async def download_zip(task_id: str):
    q = queue_manager.compression_queue
    task = q.get_task(task_id)
    if not task or task.status != TaskStatus.DONE: raise HTTPException(400)

    zip_buffer = q.build_zip(task)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="compressed.zip"'}
    )


# Endpoint dla wielu zadań (używany przez Twój JS)
@router.get("/download-multi")
async def download_multi(tasks: str = Query(...)):
    q = queue_manager.compression_queue
    task_ids = tasks.split(",")
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        found_any = False
        
        for tid in task_ids:
            task = q.get_task(tid)
            if not task or task.status != TaskStatus.DONE:
                continue
            
            # Dodajemy wszystkie pliki z tego zadania do ZIPa
            for filename, data in task.results.items():
                zf.writestr(filename, data)
                found_any = True
        
        if not found_any:
            raise HTTPException(404, "No completed tasks found to zip")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="compressed_all.zip"'}
    )



@router.post("/upload-to-drive")
async def upload_selected_to_drive(
    request: Request, 
    task_ids: list[str], 
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(request, db)
    if not user or not user.google_drive_access_token:
        raise HTTPException(401, "Google Drive not connected")

    q = queue_manager.compression_queue
    uploaded_files = []

    for tid in task_ids:
        task = q.get_task(tid)
        if not task or not task.results: continue
        
        for filename, data in task.results.items():
            print('=========upload filename==========', filename)
            # Google Drive Multipart Upload
            metadata = {"name": filename}
            files = {
                'metadata': (None, json.dumps(metadata), 'application/json'),
                'file': (filename, data)
            }
            headers = {"Authorization": f"Bearer {user.google_drive_access_token}"}
            
            r = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers=headers,
                files=files
            )

            print('=================upload_selected_to_drive============', r.json())
            
            if r.status_code == 200:
                uploaded_files.append(filename)
            elif r.status_code == 401: # Token wygasł
                raise HTTPException(401, "Token expired. Reconnect Drive.")

    return {"status": "ok", "uploaded": uploaded_files}







def download_from_drive(access_token, file_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    r = requests.get(url, headers=headers)
    return r.content




# @router.post("/video")
# async def compress_video_endpoint(file: UploadFile = File(...)):

#     data = await file.read()

#     try:
#         task_id = await video_queue_manager.video_queue.add_task(
#             file_data={"filename": file.filename, "data": data}
#         )
#         return {"task_id": task_id}

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


import uuid
import aiofiles
from pathlib import Path

@router.post("/video")
async def compress_video_endpoint(file: UploadFile = File(...)):

    try:

        suffix = Path(file.filename).suffix

        tmp_path = f"/tmp/{uuid.uuid4()}{suffix}"

        async with aiofiles.open(tmp_path, "wb") as f:

            while chunk := await file.read(1024 * 1024):
                await f.write(chunk)

        task_id = await video_queue_manager.video_queue.add_task(
            file_data={
                "filename": file.filename,
                "filepath": tmp_path
            }
        )

        return {
            "task_id": task_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )



@router.get("/video/status/{task_id}")
def video_status(task_id: str):

    task = video_queue_manager.video_queue.get_task(task_id)
    if not task:
        return JSONResponse({"error": "Task not found"}, status_code=404)

    position = video_queue_manager.video_queue.get_position(task_id)

    print(f"===Status for {task_id}: {task.compressed_size}======= ")

    return {
        "status": task.status,
        "progress": task.progress,
        "error": task.error,
        "queue_position": position,
        "compressed_size": task.compressed_size,
        "message": f"Przed tobą {position} użytkowników..." if position > 0 else "Twoje zadanie jest przetwarzane."
    }


@router.get("/video/download/{task_id}")
def download_video(task_id: str):
    task = video_queue_manager.video_queue.get_task(task_id)
    if not task or not task.result:
        raise HTTPException(status_code=404, detail="File not ready")

    return Response(
        content=task.result,
        media_type="video/mp4",
        headers={"Content-Disposition": "attachment; filename=compressed.mp4"}
    )




@router.get("/video/download-multi")
async def video_download_multi(tasks: str = Query(...)):
    q = video_queue_manager.video_queue # Upewnij się, że masz dostęp do właściwej kolejki
    task_ids = tasks.split(",")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for tid in task_ids:
            task = q.get_task(tid)
            if task and task.status == "done":
                # VideoTask przechowuje wynik w task.result (jako bytes)
                zf.writestr(task.file_data["filename"], task.result)
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="videos.zip"'})



@router.post("/video/upload-to-drive")
async def upload_video_to_drive(
    request: Request, 
    task_ids: list[str], 
    db: AsyncSession = Depends(get_db)
):
    user = await get_current_user(request, db)
    if not user or not user.google_drive_access_token:
        raise HTTPException(401, "Google Drive not connected")

    q = video_queue_manager.video_queue
    uploaded = []

    for tid in task_ids:
        task = q.get_task(tid)
        if not task or not task.result: 
            continue

        # W VideoTask używamy .file_data["filename"] oraz .result
        filename = task.file_data["filename"]
        data = task.result 

        print(f'========= Uploading video: {filename} ==========')

        # Google Drive Multipart Upload
        metadata = {"name": filename}
        files = {
            'metadata': (None, json.dumps(metadata), 'application/json'),
            'file': (filename, data)
        }
        headers = {"Authorization": f"Bearer {user.google_drive_access_token}"}
        
        try:
            r = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers=headers,
                files=files,
                timeout=60 # Wideo może być duże, dajemy więcej czasu
            )
            
            if r.status_code == 200:
                uploaded.append(filename)
                print(f'Success: {filename}')
            elif r.status_code == 401:
                raise HTTPException(401, "Token expired. Reconnect Drive.")
            else:
                print(f'Drive error {r.status_code}: {r.text}')
                
        except Exception as e:
            print(f"Request failed for {filename}: {e}")

    return {"status": "ok", "uploaded": uploaded}