from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.schemas.project import BonitaInstantiationResult, ProjectCreate
from app.services.bonita_client import instantiate_project

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
    response = await instantiate_project(payload, current_user["username"])

    return BonitaInstantiationResult(
        case_id=int(response["caseId"]),
        process_definition_id=response["processDefinitionId"],
    )
