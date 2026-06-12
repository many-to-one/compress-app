from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate
from core.security import get_password_hash
from fastapi import Depends, HTTPException, status, Request
from db.session import get_db
from jose import jwt, JWTError, ExpiredSignatureError
from core.config import settings

def decode_jwt(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

# async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
#     token = request.cookies.get("access_token")  # lub Authorization header
#     if not token:
#         return None

#     # tu Twoja logika dekodowania JWT
#     payload = decode_jwt(token)
#     user_id = payload.get("sub")

#     result = await db.execute(select(User).where(User.id == user_id))
#     return result.scalar_one_or_none()


async def get_current_user(request: Request, db: AsyncSession):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        # Dekodujemy token
        payload = decode_jwt(token)
    except ExpiredSignatureError:
        # Token wygasł - traktujemy użytkownika jako niezalogowanego
        print("DEBUG: Token wygasł")
        return None
    except JWTError:
        # Jakikolwiek inny błąd tokena (np. błędny podpis)
        print("DEBUG: Błędny token")
        return None

    user_id = payload.get("sub")
    
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()



async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# async def admin_required(
#     user: User = Depends(get_current_user)
# ):
#     if not user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required"
#         )
#     return user

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User


async def admin_required(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    user = await get_current_user(
        request,
        db
    )

    if not user:
        raise HTTPException(401, "Unauthorized")

    if not user.is_admin:
        raise HTTPException(403, "Forbidden")

    return user
