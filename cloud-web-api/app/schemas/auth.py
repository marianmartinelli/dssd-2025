from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    bonita_session_id: str | None = None  # Optional: only present when USE_BONITA=true


class LoginRequest(BaseModel):
    username: str = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, max_length=128)
