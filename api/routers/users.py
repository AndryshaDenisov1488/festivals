from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
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
        "is_admin": getattr(user, "is_admin", False),
    }
