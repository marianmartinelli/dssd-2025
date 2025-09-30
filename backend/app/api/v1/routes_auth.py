from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import authenticate_user, create_user_token

router = APIRouter()


@router.post("/login", response_model=Token, summary="Obtener token JWT")
async def login(login_request: LoginRequest) -> Token:
    try:
        user = authenticate_user(login_request.username, login_request.password)
    except HTTPException as exc:
        raise exc

    token = create_user_token(user["username"])
    return Token(access_token=token)
