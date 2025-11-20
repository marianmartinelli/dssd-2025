from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.security import get_password_hash, verify_password
from app.models.user import User

logger = get_logger()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """
    Busca un usuario por su username.

    Args:
        session: Sesión de base de datos
        username: Username del usuario a buscar

    Returns:
        Usuario encontrado o None
    """
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """
    Busca un usuario por su email.

    Args:
        session: Sesión de base de datos
        email: Email del usuario a buscar

    Returns:
        Usuario encontrado o None
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        session: Sesión de base de datos
        username: Username del nuevo usuario
        email: Email del nuevo usuario
        password: Contraseña en texto plano (será hasheada)

    Returns:
        Usuario creado
    """
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("User created", username=username, email=email)
    return user


async def authenticate_user_db(session: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    Autentica un usuario contra la base de datos.

    Args:
        session: Sesión de base de datos
        username: Username del usuario
        password: Contraseña en texto plano

    Returns:
        Usuario autenticado o None si las credenciales son inválidas
    """
    user = await get_user_by_username(session, username)
    if not user:
        logger.warning("User not found", username=username)
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning("Invalid password", username=username)
        return None

    logger.info("User authenticated successfully", username=username)
    return user
