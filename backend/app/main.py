from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.diagnosis import router as diagnosis_router
from app.api.v1.health import router as health_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.test import router as test_router
from app.core.config import settings
from app.db.session import initialize_database


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        initialize_database()

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
    app.include_router(
        chat_router,
        prefix=f"{settings.api_prefix}",
        tags=["chat"],
    )
    app.include_router(
        auth_router,
        prefix=f"{settings.api_prefix}",
        tags=["auth"],
    )
    app.include_router(
        curriculum_router,
        prefix=f"{settings.api_prefix}",
        tags=["curriculum"],
    )
    app.include_router(
        quiz_router,
        prefix=f"{settings.api_prefix}",
        tags=["quiz"],
    )
    app.include_router(
        test_router,
        prefix=f"{settings.api_prefix}",
        tags=["test"],
    )
    return app


app = create_app()
