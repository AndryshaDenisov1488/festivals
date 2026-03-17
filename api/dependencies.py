from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

import os

from database import SessionLocal
from models import User
from config import ADMIN_IDS


JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_SECRET")
JWT_ALGORITHM = "HS256"


class TokenPayload(BaseModel):
    user_id: int


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    db=Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.user_id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_current_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.user_id not in ADMIN_IDS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

