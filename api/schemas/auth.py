from datetime import datetime
from pydantic import BaseModel, EmailStr


class AuthRequestCodeIn(BaseModel):
    email: EmailStr


class AuthVerifyCodeIn(BaseModel):
    email: EmailStr
    code: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginToken(BaseModel):
    id: int
    user_id: int
    code: str
    expires_at: datetime
    used_at: datetime | None = None

