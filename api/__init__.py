import logging
import os

from fastapi import FastAPI

from .routers import auth, users, tournaments, registrations, payments, budgets, admin, exports
from .email_service import SMTP_HOST, SMTP_FROM
from config import BOT_TOKEN, CHANNEL_ID

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Judges Bot API", version="1.0.0")

    # Routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(tournaments.router, prefix="/api/v1/tournaments", tags=["tournaments"])
    app.include_router(registrations.router, prefix="/api/v1/registrations", tags=["registrations"])
    app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
    app.include_router(budgets.router, prefix="/api/v1/admin/budgets", tags=["budgets"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(exports.router, prefix="/api/v1/admin/exports", tags=["exports"])

    @app.on_event("startup")
    def on_startup():
        if not SMTP_HOST or not SMTP_FROM:
            logger.warning(
                "[SMTP] Email не настроен: SMTP_HOST и SMTP_FROM должны быть в .env. "
                "Уведомления судьям на почту не будут отправляться."
            )
        else:
            logger.info("[SMTP] Email настроен: host=%s port=%s from=%s", SMTP_HOST, os.getenv("SMTP_PORT", "587"), SMTP_FROM)

        if not BOT_TOKEN or not CHANNEL_ID:
            logger.warning(
                "[Channel] Telegram-канал не настроен: BOT_TOKEN и CHANNEL_ID должны быть в .env. "
                "Уведомления о заявках в канал не будут отправляться."
            )
        else:
            logger.info("[Channel] Telegram-канал настроен: CHANNEL_ID=%s", CHANNEL_ID)

    return app

