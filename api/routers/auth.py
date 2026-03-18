from datetime import datetime, timedelta, timezone
import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from api.schemas.auth import AuthRequestCodeIn, AuthVerifyCodeIn, AuthLoginIn, AuthSetPasswordIn, AuthChangePasswordIn, TokenOut
from api.dependencies import JWT_SECRET, JWT_ALGORITHM, get_current_user
from api.email_service import send_login_code_email


router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


@router.post("/request-code", response_model=None, status_code=204)
def request_code(payload: AuthRequestCodeIn):
    email = _normalize_email(str(payload.email))
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.email_verified.is_(True)).first()
        if not user:
            logger.info("[AUTH] request-code: email не найден или не верифицирован: %s", email)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email не найден или не привязан. Привяжите email в боте: /link_email",
            )

        now = datetime.now(timezone.utc)
        code = _generate_code()
        user.email_verification_code = code
        user.email_verification_expires_at = now + timedelta(minutes=15)
        db.commit()

        logger.info("[AUTH] request-code: код отправлен user_id=%s email=%s", user.user_id, email)
        send_login_code_email(user.email, code)
        return
    finally:
        db.close()


@router.post("/verify-code", response_model=TokenOut)
def verify_code(payload: AuthVerifyCodeIn):
    email = _normalize_email(str(payload.email))
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.info("[AUTH] verify-code: user не найден email=%s", email)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        code = user.email_verification_code
        expires_at = user.email_verification_expires_at
        now = datetime.now(timezone.utc)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if not code or code != payload.code:
            logger.info("[AUTH] verify-code: неверный/истёкший код user_id=%s email=%s", user.user_id, email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
        if expires_at and expires_at < now:
            logger.info("[AUTH] verify-code: код истёк user_id=%s email=%s", user.user_id, email)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")
        if getattr(user, "is_blocked", False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт заблокирован")

        logger.info("[AUTH] verify-code: успешный вход user_id=%s email=%s", user.user_id, email)
        token_data = {"user_id": user.user_id, "exp": now + timedelta(hours=12)}
        access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return TokenOut(access_token=access_token)
    finally:
        db.close()


@router.post("/login", response_model=TokenOut)
def login(payload: AuthLoginIn):
    email = _normalize_email(str(payload.email))
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email, User.email_verified.is_(True)).first()
        if not user:
            logger.info("[AUTH] login: пользователь не найден или email не верифицирован: %s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )
        if not user.password_hash:
            logger.info("[AUTH] login: пароль не задан user_id=%s email=%s", user.user_id, email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль не задан. Войдите по коду из почты и задайте пароль в профиле.",
            )
        if not pwd_context.verify(payload.password, user.password_hash):
            logger.info("[AUTH] login: неверный пароль user_id=%s email=%s", user.user_id, email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )
        if getattr(user, "is_blocked", False):
            logger.info("[AUTH] login: аккаунт заблокирован user_id=%s email=%s", user.user_id, email)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт заблокирован")
        logger.info("[AUTH] login: успешный вход user_id=%s email=%s", user.user_id, email)
        now = datetime.now(timezone.utc)
        token_data = {"user_id": user.user_id, "exp": now + timedelta(hours=12)}
        access_token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return TokenOut(access_token=access_token)
    finally:
        db.close()


@router.post("/set-password", response_model=None, status_code=204)
def set_password(payload: AuthSetPasswordIn, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        db_user = db.query(User).filter(User.user_id == user.user_id).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        db_user.password_hash = pwd_context.hash(payload.password)
        db.commit()
        return
    finally:
        db.close()


@router.post("/change-password", response_model=None, status_code=204)
def change_password(payload: AuthChangePasswordIn, user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        db_user = db.query(User).filter(User.user_id == user.user_id).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not db_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль не задан. Задайте пароль в профиле.",
            )
        if not pwd_context.verify(payload.current_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный текущий пароль",
            )
        db_user.password_hash = pwd_context.hash(payload.new_password)
        db.commit()
        return
    finally:
        db.close()


