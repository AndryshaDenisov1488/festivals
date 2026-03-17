from datetime import datetime, timedelta, timezone
import random
import string

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from api.schemas.auth import AuthRequestCodeIn, AuthVerifyCodeIn, TokenOut
from api.dependencies import JWT_SECRET, JWT_ALGORITHM
from api.email_service import send_login_code_email


router = APIRouter()


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@router.post("/request-code", response_model=None, status_code=204)
def request_code(payload: AuthRequestCodeIn):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.email, User.email_verified.is_(True)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found or not verified",
            )

        now = datetime.now(timezone.utc)
        code = _generate_code()
        user.email_verification_code = code
        user.email_verification_expires_at = now + timedelta(minutes=15)
        db.commit()

        send_login_code_email(user.email, code)
        return
    finally:
        db.close()


@router.post("/verify-code", response_model=TokenOut)
def verify_code(payload: AuthVerifyCodeIn):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        code = user.email_verification_code
        expires_at = user.email_verification_expires_at
        now = datetime.now(timezone.utc)

        if not code or code != payload.code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
        if expires_at and expires_at < now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

        token_data = {"user_id": user.user_id, "exp": now + timedelta(hours=12)}
        access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return TokenOut(access_token=access_token)
    finally:
        db.close()


