from api.v1.endpoints import compress_batch
from fastapi import FastAPI, Request
from api.v1.endpoints import auth

from services.queue import compression_queue
import asyncio

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Enterprise FastAPI")

templates = Jinja2Templates(directory="templates")

# statyczne pliki (JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/users", tags=["users"])
app.include_router(compress_batch.router, prefix="/compress", tags=["compress"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise FastAPI"}


@app.on_event("startup")
async def start_worker():
    asyncio.create_task(compression_queue.worker())


@app.get("/batch")
async def batch_page(request: Request):
    return templates.TemplateResponse("batch.html", {"request": request})
