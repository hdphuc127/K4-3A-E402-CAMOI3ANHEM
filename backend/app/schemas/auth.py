from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
