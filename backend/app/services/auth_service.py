from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import get_settings
from app.core.security import create_access_token
from app.services.bonita_session_manager import BonitaSessionManager
from app.services.user_service import authenticate_user_db

logger = get_logger()
settings = get_settings()


async def authenticate_user(username: str, password: str, db_session: Optional[AsyncSession] = None) -> dict:
    """
    Autentica a un usuario contra Bonita BPM o la base de datos según configuración.

    Args:
        username: Usuario
        password: Contraseña
        db_session: Sesión de base de datos (requerida si USE_BONITA=false)

    Returns:
        Diccionario con información del usuario y opcionalmente el session_id de Bonita

    Raises:
        HTTPException: Si la autenticación falla
    """
    try:
        if settings.use_bonita:
            # Autenticar contra Bonita
            session = await BonitaSessionManager.create_session(username, password)
            logger.info("User authenticated via Bonita", username=username)
            return {
                "username": username,
                "bonita_session_id": session.session_id,
            }
        else:
            # Autenticar contra la base de datos
            if db_session is None:
                raise ValueError("Database session is required when USE_BONITA is false")

            user = await authenticate_user_db(db_session, username, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            logger.info("User authenticated via database", username=username)
            return {
                "username": username,
            }
    except HTTPException:
        # Re-lanzar excepciones HTTP tal cual
        raise
    except Exception as e:
        logger.error("Authentication error", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        ) from e


def create_user_token(username: str, bonita_session_id: Optional[str] = None) -> str:
    """
    Crea un JWT con el username y opcionalmente el session ID de Bonita.

    Args:
        username: Usuario autenticado
        bonita_session_id: Session ID de Bonita (solo si USE_BONITA=true)

    Returns:
        JWT token codificado
    """
    token_lifetime = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    additional_claims = {}

    if bonita_session_id:
        additional_claims["bonita_session_id"] = bonita_session_id

    return create_access_token(
        subject=username,
        expires_delta=token_lifetime,
        additional_claims=additional_claims if additional_claims else None
    )
