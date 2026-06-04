from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
import services.queue_manager as queue_manager
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
