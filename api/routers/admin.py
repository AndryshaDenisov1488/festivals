from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import SessionLocal
from models import User, Tournament, Registration
from config import ADMIN_IDS
from api.dependencies import get_current_admin


router = APIRouter()


class BroadcastIn(BaseModel):
    message: str


@router.post("/broadcast")
async def broadcast(
    payload: BroadcastIn,
    admin: User = Depends(get_current_admin),
):
    from config import BOT_TOKEN
    if not BOT_TOKEN or not payload.message:
        raise HTTPException(status_code=400, detail="Invalid request")
    from aiogram import Bot
    bot = Bot(token=BOT_TOKEN)
    db = SessionLocal()
    try:
        users = db.query(User).all()
        ok, fail = 0, 0
        for u in users:
            try:
                await bot.send_message(u.user_id, payload.message, parse_mode="HTML")
                ok += 1
            except Exception:
                fail += 1
        return {"total": len(users), "ok": ok, "fail": fail}
    finally:
        db.close()
        await bot.session.close()
