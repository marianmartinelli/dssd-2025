from fastapi import APIRouter, Depends, status, HTTPException

from app.api.deps import get_current_user
from app.schemas.project import BonitaInstantiationResult, ProjectCreate
from app.services.bonita_client import instantiate_project
from app.services.project_service import save_project

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
