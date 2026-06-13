from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    refreshToken: str = Field(min_length=1)


class SignUpRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthResponse(BaseModel):
    user: UserResponse
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresIn: int
