from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select
from fastapi import HTTPException, status
import structlog

from app.models.organization import Organization

logger = structlog.get_logger()


async def create_organization(
    name: str,
    description: str | None,
    session: AsyncSession
) -> Organization:
    """
    Crea una nueva organización.

    Args:
        name: Nombre único de la organización (3-150 chars)
        description: Descripción opcional (max 500 chars)
        session: Sesión de base de datos

    Returns:
        Organization: La organización creada

    Raises:
        HTTPException 409: Si ya existe una organización con ese nombre
        HTTPException 500: Error interno al crear
    """
    try:
        # Verificar si ya existe una organización con ese nombre
        stmt = select(Organization).where(Organization.name == name)
        result = await session.execute(stmt)
        existing_org = result.scalar_one_or_none()

        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una organización con el nombre '{name}'"
            )

        # Crear nueva organización
        new_org = Organization(
            name=name,
            description=description
        )

        session.add(new_org)
        await session.commit()
        await session.refresh(new_org)

        logger.info("Organization created", organization_id=new_org.id, name=new_org.name)
        return new_org

    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        logger.error("Error creating organization", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la organización: {str(exc)}"
        )


async def list_organizations(session: AsyncSession) -> List[Organization]:
    """
    Lista todas las organizaciones.

    Args:
        session: Sesión de base de datos

    Returns:
        List[Organization]: Lista de todas las organizaciones

    Raises:
        HTTPException 500: Error interno al listar
    """
    try:
        stmt = select(Organization).order_by(Organization.name)
        result = await session.execute(stmt)
        organizations = result.scalars().all()

        return list(organizations)

    except Exception as exc:
        logger.error("Error listing organizations", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar organizaciones: {str(exc)}"
        )
