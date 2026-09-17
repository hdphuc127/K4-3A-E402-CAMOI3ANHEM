from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.diagnosis import router as diagnosis_router
from app.api.v1.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, tags=["health"])
    app.include_router(
        health_router,
        prefix=f"{settings.api_prefix}",
        tags=["health"],
    )
    app.include_router(
        diagnosis_router,
        prefix=f"{settings.api_prefix}",
        tags=["diagnosis"],
    )

    return app


app = create_app()
