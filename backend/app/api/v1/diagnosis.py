from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.pipelines.mistake_diagnosis import diagnose_mistake
from app.schemas.common import ApiResponse, ResponseMeta
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult

router = APIRouter()


@router.post("/diagnosis", response_model=ApiResponse[DiagnosisResult])
def create_diagnosis(
    request: DiagnosisRequest,
) -> ApiResponse[DiagnosisResult]:
    result = diagnose_mistake(request)
    return ApiResponse(
        success=True,
        data=result,
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )
