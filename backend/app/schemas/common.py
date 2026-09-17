from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ApiError(BaseModel):
    code: str
    message: str
    details: str | None = None


class ResponseMeta(BaseModel):
    timestamp: datetime
    request_id: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)


class ApiResponse(BaseModel, Generic[DataT]):
    success: bool
    data: DataT | None
    error: ApiError | None
    meta: ResponseMeta
