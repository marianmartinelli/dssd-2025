from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.services import organization_service

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva organización"
)
async def create_organization(
    payload: OrganizationCreate,
    db_session: AsyncSession = Depends(get_db_session)
) -> OrganizationResponse:
    """
    Crea una nueva organización.

    **⚠️ SIN AUTENTICACIÓN**: Por ahora es público para simplificar desarrollo.

    **Campos requeridos**:
    - `name`: Nombre único de la organización (3-150 caracteres)

    **Campos opcionales**:
    - `description`: Descripción de la organización (máximo 500 caracteres)

    **Validaciones**:
    - El nombre debe ser único en el sistema
    - Retorna 409 Conflict si ya existe

    **🔒 Futuro**: Solo administradores podrán crear organizaciones.
    Agregar: `current_user: Dict = Depends(get_current_admin_user)`
    """
    organization = await organization_service.create_organization(
        name=payload.name,
        description=payload.description,
        session=db_session
    )

    return OrganizationResponse.model_validate(organization)


@router.get(
    "",
    response_model=List[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las organizaciones"
)
async def list_organizations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> List[OrganizationResponse]:
    """
    Lista todas las organizaciones disponibles en el sistema.

    **Requiere autenticación**: Usuario debe estar autenticado.

    **Retorna**: Lista ordenada alfabéticamente por nombre.

    **Nota**: En el futuro, puede que solo administradores puedan listar organizaciones.
    """
    organizations = await organization_service.list_organizations(session=db_session)

    return [OrganizationResponse.model_validate(org) for org in organizations]
