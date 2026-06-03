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





from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
import services.queue_manager as queue_manager
from services.queue import TaskStatus
import zipfile

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


def download_from_drive(access_token, file_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    r = requests.get(url, headers=headers)
    return r.content


def upload_to_drive(access_token, folder_id, filename, file_bytes):
    headers = {"Authorization": f"Bearer {access_token}"}
    metadata = {"name": filename, "parents": [folder_id]}

    files = {
        "metadata": ("metadata", json.dumps(metadata), "application/json"),
        "file": (filename, file_bytes)
    }

    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers=headers,
        files=files
    )
    return r.json()