from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    # full_name: str | None = None

    @validator("password")
    def validate_password(cls, v):
        if not isinstance(v, str):
            raise ValueError("Password must be a string")
        if len(v.encode("utf-8")) > 128:
            raise ValueError("Password too long")
        return v

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str 


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str