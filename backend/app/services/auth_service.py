from app.core.security import create_access_token, hash_password, verify_password
from app.db.users import UserRecord, create_user, get_user_by_email
from app.schemas.auth import AuthToken, UserProfile


def register_user(email: str, full_name: str, password: str) -> AuthToken:
    user = create_user(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    return _build_auth_token(user)


def authenticate_user(email: str, password: str) -> AuthToken | None:
    user = get_user_by_email(email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return _build_auth_token(user)


def user_to_profile(user: UserRecord) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
    )


def _build_auth_token(user: UserRecord) -> AuthToken:
    return AuthToken(
        access_token=create_access_token(user_id=user.id, email=user.email),
        user=user_to_profile(user),
    )
