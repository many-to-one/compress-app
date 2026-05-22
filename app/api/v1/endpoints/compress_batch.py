# FILE: routes/compress_batch.py
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from services.queue import compression_queue, TaskStatus
from io import BytesIO

router = APIRouter()

@router.post("/batch")
async def compress_batch(files: list[UploadFile]):
    if not files:
        raise HTTPException(400, "No files uploaded")

    file_data = []
    for f in files:
        file_data.append((f.filename, await f.read()))

    task_id = await compression_queue.add_task(file_data)
    return {"task_id": task_id}


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    task = compression_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    return {
        "status": task.status,
        "progress": task.progress,
        "error": task.error,
        "files": list(task.results.keys())
    }


@router.get("/download/{task_id}")
async def download_zip(task_id: str):
    task = compression_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status != TaskStatus.DONE:
        raise HTTPException(400, "Task not finished")

    zip_bytes = compression_queue.build_zip(task)

    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=compressed_{task_id}.zip"}
    )
