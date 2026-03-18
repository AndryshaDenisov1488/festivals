from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class AuthRequestCodeIn(BaseModel):
    email: EmailStr


class AuthVerifyCodeIn(BaseModel):
    email: EmailStr
    code: str


class AuthLoginIn(BaseModel):
    email: EmailStr
    password: str


class AuthSetPasswordIn(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginToken(BaseModel):
    id: int
    user_id: int
    code: str
    expires_at: datetime
    used_at: datetime | None = None

