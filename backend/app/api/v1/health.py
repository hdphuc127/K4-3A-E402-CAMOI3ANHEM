from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import ApiResponse, ResponseMeta
from app.schemas.health import HealthStatus

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthStatus])
def get_health() -> ApiResponse[HealthStatus]:
    now = datetime.now(timezone.utc)
    return ApiResponse(
        success=True,
        data=HealthStatus(
            service=settings.app_name,
            environment=settings.app_env,
            status="ok",
        ),
        error=None,
        meta=ResponseMeta(timestamp=now),
    )
