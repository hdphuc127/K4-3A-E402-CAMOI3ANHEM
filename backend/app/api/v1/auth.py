from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.db.users import UserRecord
from app.schemas.auth import AuthToken, LoginRequest, RegisterRequest, UserProfile
from app.schemas.common import ApiResponse, ResponseMeta
from app.services.auth_service import (
    authenticate_user,
    register_user,
    user_to_profile,
)

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=ApiResponse[AuthToken])
def register(request: RegisterRequest) -> ApiResponse[AuthToken]:
    try:
        auth_token = register_user(
            email=str(request.email),
            full_name=request.full_name,
            password=request.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ApiResponse(
        success=True,
        data=auth_token,
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )


@router.post("/login", response_model=ApiResponse[AuthToken])
def login(request: LoginRequest) -> ApiResponse[AuthToken]:
    auth_token = authenticate_user(str(request.email), request.password)
    if auth_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return ApiResponse(
        success=True,
        data=auth_token,
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )


@router.get("/me", response_model=ApiResponse[UserProfile])
def me(
    current_user: UserRecord = Depends(get_current_user),
) -> ApiResponse[UserProfile]:
    return ApiResponse(
        success=True,
        data=user_to_profile(current_user),
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )
