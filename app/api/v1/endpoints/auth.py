from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from schemas.user import User, UserCreate, Token, LoginSchema, ResetPasswordSchema, ForgotPasswordSchema
from crud.user import get_user_by_email, create_user, get_current_user, admin_required
from core.security import verify_password, create_access_token, create_reset_token
from core.config import settings

import urllib
import uuid
import smtplib
from email.mime.text import MIMEText

SMTP_PASSWORD = settings.SMTP_PASSWORD
EMAIL = settings.EMAIL
RESET_URL = settings.RESET_URL
EMAIL_FROM = settings.EMAIL_FROM

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db, user)

# @router.post("/token", response_model=Token)
# async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
#     user = await get_user_by_email(db, form_data.username)
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=User)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(db, user=user_in)


from fastapi.responses import JSONResponse

@router.post("/login")
async def login(user: LoginSchema, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(400, "Invalid credentials")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(400, "Invalid credentials")

    token = create_access_token({"sub": str(db_user.id)})

    response = JSONResponse({
        "success": True
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24
    )

    return response



@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login_page", status_code=302)
    response.delete_cookie("access_token")
    return response



@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db)
):

    email = verify_reset_token(data.token)

    if not email:
        raise HTTPException(400, "Invalid token")

    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(400, "User not found")

    user.hashed_password = hash_password(data.new_password)

    await db.commit()

    return {
        "message": "Password updated"
    }


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db)
):

    user = await get_user_by_email(db, data.email)

    # NIE ujawniaj czy email istnieje
    if user:

        token = create_reset_token(user.email)

        reset_link = f"{RESET_URL}{token}"
        print("RESET LINK:", reset_link)  # debug

        msg = MIMEText(f"Reset password link: {reset_link}")
        msg["Subject"] = "Password reset"
        msg["From"] = EMAIL_FROM
        msg["To"] = user.email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, SMTP_PASSWORD)
            smtp.send_message(msg)

        print(f"Email resetujący wysłany do {user.email}")

    return {
        "message": "If account exists, reset email was sent"
    }


# -------------------------
    # Reset hasła
    # -------------------------
    # async def on_after_forgot_password(self, user: User, token: str, request=None):
    #     reset_link = f"{RESET_URL}{token}"
    #     print("RESET LINK:", reset_link)  # debug

    #     msg = MIMEText(f"Reset password link: {reset_link}")
    #     msg["Subject"] = "Password reset"
    #     msg["From"] = EMAIL_FROM
    #     msg["To"] = user.email

    #     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    #         smtp.login(EMAIL, SMTP_PASSWORD)
    #         smtp.send_message(msg)

    #     print(f"Email resetujący wysłany do {user.email}")


from sqlalchemy import select # upewnij się, że masz ten import

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/admin/block_user/{user_id}", response_model=None)
async def block_user(
    user_id: int, 
    admin: Any = Depends(admin_required), # Zmieniamy User na Any
    db: Any = Depends(get_db)             # Zmieniamy AsyncSession na Any
) -> Any:                                 # Dodajemy jawnie -> Any
    """
    Używamy Any w parametrach, aby Pydantic nie próbował 
    budować modelu walidacyjnego z klas SQLAlchemy.
    """
    # Rzutowanie typu dla edytora (opcjonalne, dla podpowiadania składni)
    db_session: AsyncSession = db 

    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    user.is_blocked = True
    if hasattr(user, 'ips') and user.ips:
        user.blocked_ips = list(set(user.ips))
    
    db_session.add(user)
    await db_session.commit()

    return {"status": "blocked", "user_id": user_id}



# ===================================
# Google OAuth2
# ===================================
SCOPES = [
    "openid",
    "email",
    "profile"
]

@router.get("/google")
def google_login():
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    print("GOOGLE_OAUTH_CLIENT_ID", settings.GOOGLE_OAUTH_CLIENT_ID)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/google/callback")
def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    # 1. Pobierz tokeny
    token_res = requests.post(token_url, data=data).json()
    access_token = token_res["access_token"]

    # 2. Pobierz dane użytkownika
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = userinfo["email"]
    name = userinfo.get("name", "")
    picture = userinfo.get("picture", "")

    # 3. Sprawdź czy użytkownik istnieje w DB
    user = get_or_create_user(email=email, name=name, avatar=picture)

    # 4. Wygeneruj JWT dla Twojej aplikacji
    jwt_token = create_jwt_for_user(user)

    # 5. Ustaw cookie i przekieruj do panelu
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    return response


# ===========================
# Google Drive OAuth2
# ===========================
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive.file"
]

@router.get("/auth/google-drive")
def google_drive_auth():
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/google-drive/callback")
def google_drive_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    r = requests.post(token_url, data=data)
    tokens = r.json()

    # Zapisz access_token + refresh_token do DB
    # tokens["access_token"]
    # tokens["refresh_token"]

    return {"status": "connected", "tokens": tokens}