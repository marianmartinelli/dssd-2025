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
            from app.services.bonita_client import BonitaUserService
            
            session = await BonitaSessionManager.create_session(username, password)
            
            # Obtener rol del usuario
            role = await BonitaUserService.get_user_role(session)
            
            logger.info("User authenticated via Bonita", username=username, role=role)
            return {
                "username": username,
                "bonita_session_id": session.session_id,
                "role": role,
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

            logger.info("User authenticated via database", username=username, user_id=user.id)
            return {
                "user_id": user.id,
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


def create_user_token(user_id: Optional[int] = None, username: Optional[str] = None, bonita_session_id: Optional[str] = None, role: Optional[str] = None) -> str:
    """
    Crea un JWT con el user_id (o username si usa Bonita) y opcionalmente el session ID de Bonita.

    Args:
        user_id: ID del usuario autenticado (requerido si USE_BONITA=false)
        username: Usuario autenticado (usado como fallback si USE_BONITA=true y no hay user_id)
        bonita_session_id: Session ID de Bonita (solo si USE_BONITA=true)
        role: Rol del usuario en Bonita (solo si USE_BONITA=true)

    Returns:
        JWT token codificado
    """
    token_lifetime = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    additional_claims = {}

    if bonita_session_id:
        additional_claims["bonita_session_id"] = bonita_session_id
    
    if role:
        additional_claims["role"] = role

    # Usar user_id como subject si está disponible, sino usar username
    subject = str(user_id) if user_id is not None else username

    if subject is None:
        raise ValueError("Either user_id or username must be provided")

    return create_access_token(
        subject=subject,
        expires_delta=token_lifetime,
        additional_claims=additional_claims if additional_claims else None
    )
