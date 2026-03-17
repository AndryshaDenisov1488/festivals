from fastapi import FastAPI

from .routers import auth, users, tournaments, registrations, payments, budgets, admin, exports


def create_app() -> FastAPI:
    app = FastAPI(title="Judges Bot API", version="1.0.0")

    # Routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(tournaments.router, prefix="/api/v1/tournaments", tags=["tournaments"])
    app.include_router(registrations.router, prefix="/api/v1/registrations", tags=["registrations"])
    app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
    app.include_router(budgets.router, prefix="/api/v1", tags=["budgets"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(exports.router, prefix="/api/v1/admin/exports", tags=["exports"])

    return app

