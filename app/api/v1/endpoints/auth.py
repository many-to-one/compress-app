from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from schemas.user import User, UserCreate, Token, LoginSchema
from crud.user import get_user_by_email, create_user
from core.security import verify_password, create_access_token, create_reset_token
from core.config import mail_conf

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

    token = create_access_token({"sub": db_user.email})

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

        reset_link = f"http://localhost:8000/reset-password?token={token}"

        message = MessageSchema(
            subject="Reset password",
            recipients=[user.email],
            body=f"""
            Click link to reset password:

            {reset_link}
            """,
            subtype="plain"
        )

        fm = FastMail(mail_conf)

        await fm.send_message(message)

    return {
        "message": "If account exists, reset email was sent"
    }