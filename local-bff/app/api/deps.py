from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import decode_token
from app.models.user import User
from app.services.bonita_client import BonitaClient
from app.services.bonita_session_manager import BonitaSession, BonitaSessionManager

logger = get_logger()
settings = get_settings()
reusable_oauth2 = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(reusable_oauth2),
    db_session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Extrae y valida el usuario actual del JWT token.

    Si USE_BONITA=false, consulta el User completo de la base de datos.
    Si USE_BONITA=true, retorna username y bonita_session_id del token.

    Returns:
        Diccionario con id, username, email, organization_id y opcionalmente bonita_session_id
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Si USE_BONITA está deshabilitado, subject es user_id, consultar User de la DB
    if not settings.use_bonita:
        try:
            user_id = int(subject)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

        stmt = select(User).where(User.id == user_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "organization_id": user.organization_id,
        }

    # Si USE_BONITA está habilitado, subject es username
    bonita_session_id = payload.get("bonita_session_id")
    if bonita_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing Bonita session"
        )

    return {
        "username": subject,
        "bonita_session_id": bonita_session_id,
    }


async def get_bonita_session(current_user: Dict[str, Any] = Depends(get_current_user)) -> BonitaSession:
    """
    Obtiene la sesión persistente de Bonita para el usuario actual.

    Returns:
        Sesión de Bonita autenticada y activa

    Raises:
        HTTPException: Si la sesión no existe o expiró o si Bonita está deshabilitado
    """
    if not settings.use_bonita:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bonita integration is disabled"
        )

    bonita_session_id = current_user.get("bonita_session_id")
    if not bonita_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bonita session not found in token"
        )

    # Obtener la sesión del manager (lanza excepción si no existe o expiró)
    session = await BonitaSessionManager.get_session(bonita_session_id)

    return session


async def get_bonita_client(current_user: Dict[str, Any] = Depends(get_current_user)) -> BonitaClient:
    """
    Crea un cliente de Bonita usando la sesión persistente del usuario actual.

    Returns:
        Cliente de Bonita listo para usar

    Raises:
        HTTPException: Si la sesión no existe o expiró o si Bonita está deshabilitado
    """
    session = await get_bonita_session(current_user)
    return BonitaClient(session)
