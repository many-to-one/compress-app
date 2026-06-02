# main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from jose import jwt, JWTError

from api.v1.endpoints import auth, admin, compress_batch
from crud.user import get_current_user
from db.session import get_db, AsyncSessionLocal
from core.config import settings
# from services.queue import compression_queue

import asyncio
import aioredis
import httpx
import time


# ============================
# APP
# ============================

app = FastAPI(title="Enterprise FastAPI")

templates = Jinja2Templates(directory="templates")

# print(">>> MIDDLEWARE REGISTRATION START <<<")



# ============================
# REDIS
# ============================

redis = aioredis.from_url(
    "redis://redis:6379",
    decode_responses=True
)


# ============================
# PUBLIC ROUTES
# ============================

PUBLIC_PATHS = {
    "/login_page",
    "/register_page",
    "/forgot_password",
    "/auth/login",
    "/auth/register",
    "/auth/logout",
    "/auth/forgot-password",
    "/auth/reset-password",
}

PUBLIC_PREFIXES = [
    "/static",
]
























# ============================
# DATACENTER DETECTION
# ============================

ipinfo_cache = {}
IPINFO_TTL = 86400


async def is_datacenter_ip(ip: str):

    if (
        ip.startswith("172.")
        or ip.startswith("10.")
        or ip.startswith("192.168.")
    ):
        return False

    now = time.time()

    cached = ipinfo_cache.get(ip)

    if cached and now - cached["ts"] < IPINFO_TTL:
        return cached["dc"]

    try:

        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(f"https://ipinfo.io/{ip}/json")

        org = r.json().get("org", "").lower()

    except Exception:

        ipinfo_cache[ip] = {
            "ts": now,
            "dc": False
        }

        return False

    dc = any(x in org for x in [
        "aws",
        "amazon",
        "google",
        "ovh",
        "hetzner",
        "digitalocean"
    ])

    ipinfo_cache[ip] = {
        "ts": now,
        "dc": dc
    }

    return dc



# 7 ============================
# ADMIN PROTECT
# ============================
# print("REGISTERING: admin_protect")
@app.middleware("http")
async def admin_protect(request: Request, call_next):

    if request.url.path.startswith("/admin"):

        user = request.state.user

        if not user or not user.is_admin:

            return templates.TemplateResponse(
                "403.html",
                {
                    "request": request
                },
                status_code=403
            )

    return await call_next(request)



# 6 ============================
# USER/IP SECURITY MIDDLEWARE
# ============================
# print("REGISTERING: user_security_middleware")
@app.middleware("http")
async def user_security_middleware(request: Request, call_next):

    # print("REGISTERING: user_security_middleware db", request.state.db)
    db = request.state.db
    user = request.state.user
    ip = request.client.host

    # Jeśli user nie istnieje → po prostu przepuszczamy
    if not user:
        return await call_next(request)

    # ===== SAVE IPS =====
    if user.ips is None:
        user.ips = []

    if ip not in user.ips:
        user.ips.append(ip)
        flag_modified(user, "ips")
        db.add(user)
        await db.commit()

    # ===== USER BLOCKED =====
    if user.is_blocked:
        if user.blocked_ips is None:
            user.blocked_ips = []
        if ip not in user.blocked_ips:
            user.blocked_ips.append(ip)
            flag_modified(user, "blocked_ips")
            db.add(user)
            await db.commit()

        return templates.TemplateResponse(
            "blocked.html",
            {"request": request},
            status_code=403
        )

    # ===== BLOCKED IP =====
    if user.blocked_ips and ip in user.blocked_ips:
        return templates.TemplateResponse(
            "blocked.html",
            {"request": request},
            status_code=403
        )

    # TYLKO JEDEN call_next
    return await call_next(request)



# 5 ============================
# AUTH MIDDLEWARE
# ============================
# print("REGISTERING: auth_middleware")
@app.middleware("http")
async def auth_middleware(request: Request, call_next):

    path = request.url.path

    # PUBLIC
    if (
        path in PUBLIC_PATHS
        or any(path.startswith(p) for p in PUBLIC_PREFIXES)
    ):
        return await call_next(request)

    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(
            url="/login_page",
            status_code=302
        )

    try:
        jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

    except JWTError:

        response = RedirectResponse(
            url="/login_page",
            status_code=302
        )

        response.delete_cookie("access_token")

        return response

    return await call_next(request)



# 4 ============================
# NETWORK SECURITY
# ============================
# print("REGISTERING: security_middleware")
@app.middleware("http")
async def security_middleware(request: Request, call_next):

    ip = request.client.host

    path = request.url.path

    # static/login bypass
    if (
        path in PUBLIC_PATHS
        or any(path.startswith(p) for p in PUBLIC_PREFIXES)
    ):
        return await call_next(request)

    # datacenter/vpn
    if await is_datacenter_ip(ip):

        return templates.TemplateResponse(
            "blocked.html",
            {
                "request": request
            },
            status_code=403
        )

    return await call_next(request)



# 3 ============================
# RATE LIMIT
# ============================
# print("REGISTERING: redis_rate_limit")
@app.middleware("http")
async def redis_rate_limit(request: Request, call_next):

    ip = request.client.host

    key = f"rl:{ip}"

    count = await redis.incr(key)

    if count == 1:
        await redis.expire(key, 10)

    if count > 100:

        user = getattr(request.state, "user", None)

        if user:

            user.is_blocked = True

            request.state.db.add(user)

            await request.state.db.commit()

        return Response(
            "Too many requests",
            status_code=429
        )

    return await call_next(request)


# 2 ============================
# LOAD USER MIDDLEWARE
# ============================
# print("REGISTERING: load_user_middleware")
@app.middleware("http")
async def load_user_middleware(request: Request, call_next):

    request.state.user = None

    token = request.cookies.get("access_token")

    if token:
        try:
            user = await get_current_user(
                request,
                request.state.db
            )

            request.state.user = user

        except Exception:
            request.state.user = None

    return await call_next(request)



# 1 ============================
# DB SESSION MIDDLEWARE
# MUSI BYĆ PIERWSZY
# ============================

# print("REGISTERING: db_session_middleware")
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):

    async with AsyncSessionLocal() as db:

        request.state.db = db
        # print("REGISTERING: db_session_middleware", request.state.db)

        response = await call_next(request)

        return response


# ============================
# STATIC
# ============================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ============================
# ROUTERS
# ============================

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    compress_batch.router,
    prefix="/compress",
    tags=["compress"]
)

app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)


# ============================
# STARTUP
# ============================

# @app.on_event("startup")
# async def start_worker():

#     asyncio.create_task(
#         compression_queue.worker()
#     )


# ============================
# PAGES
# ============================

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = request.state.user

    return templates.TemplateResponse(
        request=request,
        name="batch.html",
        context={
            "request": request,
            "is_authenticated": bool(user),
            "is_admin": bool(user and user.is_admin),
            "user": user
        }
    )


@app.get("/login_page")
async def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )


@app.get("/register_page")
async def register_page(request: Request):

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request
        }
    )


@app.get("/forgot_password")
async def forgot_password_page(request: Request):

    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request
        }
    )



import asyncio
import services.queue_manager as queue_holder
from services.queue import CompressionQueue


@app.on_event("startup")
async def start_worker():
    # 1. Utwórz kolejkę
    queue_holder.compression_queue = CompressionQueue()

    # 2. Uruchom worker w tle
    asyncio.create_task(queue_holder.compression_queue.worker())



# import asyncio

# import services.queue_manager as queue_manager

# from services.queue import CompressionQueue

# @app.on_event("startup")
# async def startup():

#     queue_manager.compression_queue = CompressionQueue()

#     asyncio.create_task(
#         queue_manager.compression_queue.worker()
#     )

