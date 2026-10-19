from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import WEB_PORTAL_URL

from . import create_app


def get_application() -> FastAPI:
    app = create_app()

    # Basic CORS setup – can be tightened later via env
    origins = []
    portal = (WEB_PORTAL_URL or "").rstrip("/")
    if portal:
        origins.append(portal)
        if portal.startswith("https://") and "://www." not in portal:
            origins.append(portal.replace("https://", "https://www.", 1))
    origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = get_application()

