from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import create_app


def get_application() -> FastAPI:
    app = create_app()

    # Basic CORS setup – can be tightened later via env
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = get_application()

