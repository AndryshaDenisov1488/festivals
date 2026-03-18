from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from config import ADMIN_IDS
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
