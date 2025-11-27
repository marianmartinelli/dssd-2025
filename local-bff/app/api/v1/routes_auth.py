from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_session
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse, SetUserOrganizationRequest
from app.services.auth_service import authenticate_user, create_user_token
from app.services.bonita_session_manager import BonitaSessionManager
from app.models.user import User

logger = structlog.get_logger()

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


@router.get("/me", response_model=UserResponse, summary="Obtener información del usuario actual")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> UserResponse:
    """
    Obtiene información del usuario autenticado actual (Bonita).
    Retorna username y organización si está configurada en la DB.
    """
    try:
        username = current_user.get("username")

        # Buscar usuario en DB local
        stmt = select(User).where(
            User.username == username
        ).options(selectinload(User.organization))

        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        return UserResponse(
            username=username,
            email=user.email if user else None,
            organization_name=user.organization.name if user and user.organization else None
        )
    except Exception as e:
        logger.error("Error fetching current user info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información del usuario: {str(e)}"
        )


@router.post("/user/organization", status_code=status.HTTP_200_OK, summary="Configurar organización del usuario")
async def set_user_organization(
    request: SetUserOrganizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Configura la organización del usuario de Bonita en la DB local.
    Permite asociar un usuario de Bonita con una organización.
    """
    try:
        username = current_user.get("username")

        # Verificar que la organización existe
        from app.models.organization import Organization
        org = await db_session.get(Organization, request.organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organización no encontrada"
            )

        # Buscar usuario en DB local
        stmt = select(User).where(User.username == username)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Actualizar organización del usuario existente
            user.organization_id = request.organization_id
        else:
            # Crear nuevo usuario en DB local (solo para usuarios Bonita)
            # Necesitamos un password dummy ya que no lo usaremos
            user = User(
                username=username,
                email=f"{username}@bonita.local",  # Email dummy
                hashed_password="bonita_user_no_password",  # Password dummy
                organization_id=request.organization_id
            )
            db_session.add(user)

        await db_session.commit()
        await db_session.refresh(user)

        return {
            "message": "Organización configurada exitosamente",
            "username": username,
            "organization_id": request.organization_id
        }
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        logger.error("Error setting user organization", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al configurar organización: {str(e)}"
        )
