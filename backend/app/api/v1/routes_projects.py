from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user, get_bonita_client
from app.core.config import get_settings
from app.core.database import get_db_session
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.bonita_client import instantiate_project, BonitaClient
from app.services.project_service import save_project, list_projects

router = APIRouter()
settings = get_settings()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto",
)
async def create_project(
    payload: ProjectCreate,
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """
    Crea un nuevo proyecto.

    Según la configuración USE_BONITA:
    - Si USE_BONITA=true: instancia el proceso en Bonita y guarda en DB con case_id
    - Si USE_BONITA=false: solo guarda en DB con case_id=null

    Retorna el proyecto completo con sus work_plan_stages.
    """
    try:
        case_id: Optional[int] = None

        if settings.use_bonita:
            # Obtener cliente de Bonita y crear caso
            bonita_client = await get_bonita_client(current_user)
            response = await instantiate_project(bonita_client, payload, current_user["username"])

            # Validar respuesta
            if not response or not response.get("caseId"):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from Bonita: Missing caseId",
                )

            case_id = int(response["caseId"])

        # Guardar proyecto en la base de datos (con o sin case_id)
        project = await save_project(payload, current_user, db_session, case_id=case_id)

        return ProjectResponse.model_validate(project)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
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
