from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_session
from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import authenticate_user, create_user_token
from app.services.bonita_session_manager import BonitaSessionManager

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=Token, summary="Obtener token JWT")
async def login(
    login_request: LoginRequest,
    db_session: AsyncSession = Depends(get_db_session)
) -> Token:
    """
    Autentica al usuario y devuelve un JWT token.

    Según la configuración USE_BONITA:
    - Si USE_BONITA=true: autentica contra Bonita BPM, token incluye bonita_session_id
    - Si USE_BONITA=false: autentica contra la base de datos, token solo incluye username

    La sesión de Bonita (si aplica) se mantiene activa en el servidor hasta que expire el JWT.
    """
    try:
        user = await authenticate_user(
            login_request.username,
            login_request.password,
            db_session=db_session if not settings.use_bonita else None
        )
    except HTTPException as exc:
        raise exc

    # Crear token con user_id (si está disponible) o username, y opcionalmente bonita_session_id
    token = create_user_token(
        user_id=user.get("user_id"),
        username=user.get("username"),
        bonita_session_id=user.get("bonita_session_id")
    )
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    """
    Cierra la sesión del usuario.

    Si USE_BONITA=true: limpia la sesión de Bonita del servidor
    Si USE_BONITA=false: simplemente retorna 204 (el cliente debe descartar el JWT)

    El JWT seguirá siendo válido hasta que expire.
    """
    if settings.use_bonita:
        bonita_session_id = current_user.get("bonita_session_id")
        if bonita_session_id:
            try:
                await BonitaSessionManager.remove_session(bonita_session_id)
            except Exception:
                # Si la sesión no existe o ya fue removida, no es un error crítico
                pass

    return None
