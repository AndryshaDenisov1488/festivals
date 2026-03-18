from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.schemas.users import ProfileUpdateIn
from config import ADMIN_IDS
from database import SessionLocal
from models import User


router = APIRouter()


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "function": user.function,
        "category": user.category,
        "email": getattr(user, "email", None),
        "is_admin": user.user_id in ADMIN_IDS,
        "has_password": getattr(user, "password_hash", None) is not None,
    }


@router.patch("/me", status_code=204)
def update_me(payload: ProfileUpdateIn, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.user_id == user.user_id).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        db_user.first_name = payload.first_name
        db_user.last_name = payload.last_name
        db_user.function = payload.function
        db_user.category = payload.category
        db.commit()
        return
    finally:
        db.close()
