from api.v1.endpoints import compress_batch
from fastapi import FastAPI, Request
from api.v1.endpoints import auth
from core.config import settings

from services.queue import compression_queue
import asyncio

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware import Middleware
from fastapi.responses import RedirectResponse, HTMLResponse
from jose import jwt, JWTError

app = FastAPI(title="Enterprise FastAPI")

templates = Jinja2Templates(directory="templates")

PUBLIC_PATHS = {
    "/", 
    "/login_page",
    "/register_page",
    "/forgot_page",
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
    "/forgot_password",
}

PUBLIC_PREFIXES = [
    "/reset_password",   # <-- tu obsługujemy token w query
    "/static",
]

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # pełne ścieżki
    if path in PUBLIC_PATHS:
        return await call_next(request)

    # prefixy (np. /reset-password?token=...)
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return await call_next(request)

    # sprawdzamy ciasteczko
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/login_page")

    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return RedirectResponse("/login_page")

    return await call_next(request)



# statyczne pliki (JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/users", tags=["users"])
app.include_router(compress_batch.router, prefix="/compress", tags=["compress"])


@app.on_event("startup")
async def start_worker():
    asyncio.create_task(compression_queue.worker())


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    token = request.cookies.get("access_token")

    return templates.TemplateResponse(
        request=request,
        name="batch.html",
        context={
            "is_authenticated": bool(token)
        }
    )

@app.get("/login_page")
async def batch_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register_page")
async def batch_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/forgot_password")
async def forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})