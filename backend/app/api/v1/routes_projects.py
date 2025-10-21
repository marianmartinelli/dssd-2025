from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.schemas.project import BonitaInstantiationResult, ProjectCreate, ProjectResponse
from app.services.bonita_client import instantiate_project
from app.services.project_service import save_project, list_projects

router = APIRouter()


@router.post(
    "",
    response_model=BonitaInstantiationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Crear caso de proyecto en Bonita",
)
async def create_project(
    payload: ProjectCreate,
    current_user=Depends(get_current_user),
) -> BonitaInstantiationResult:
    try:
        response = await instantiate_project(payload, current_user["username"])

        # Valida respuesta
        if not response or not response.get("caseId"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from Bonita: Missing caseId",
            )

        await save_project(payload, response, current_user)

        return BonitaInstantiationResult(
            case_id=int(response["caseId"]),
            process_definition_id=response["processDefinitionId"],
        )

    except HTTPException as http_exc:
        # Manejar errores específicos de Bonita
        raise http_exc

    except Exception as e:
        # Manejar errores inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos los proyectos con sus etapas",
)
async def get_projects(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[ProjectResponse]:
    """
    Lista todos los proyectos registrados con sus respectivas etapas del plan de trabajo.

    Requiere autenticación JWT.
    """
    try:
        projects = await list_projects(session)
        return [ProjectResponse.model_validate(project) for project in projects]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar proyectos: {str(e)}",
        )
