from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None


class LoginRequest(BaseModel):
    username: str = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, max_length=128)
