from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user, get_bonita_client
from app.core.config import get_settings
from app.core.database import get_db_session
from app.schemas.project import ProjectCreate, ProjectResponse, CollaborationRequestCreate, CollaborationRequestResponse, WorkPlanStageResponse, ObservationCreate, ObservationResponse
from app.services.bonita_client import instantiate_project, BonitaClient, instantiate_observation
from app.services.project_service import save_project, list_projects, create_collaboration_request, list_collaboration_requests_by_project, get_project_by_id, get_project_by_external_ref, get_observation_by_external_ref, get_collaboration_by_external_ref, commit_collaboration_request, complete_collaboration_request, complete_work_plan_stage, save_observation, list_observation_by_project, resolve_observation as resolve_observation_service

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
    summary="Listar proyectos con filtros opcionales",
)
async def get_projects(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    status_filter: Optional[str] = None,
    owner_only: bool = False,
) -> List[ProjectResponse]:
    """
    Lista proyectos con filtros opcionales.

    Filtros automáticos:
    - Los proyectos se filtran por la organización del usuario autenticado.

    Query parameters:
    - status_filter: Filtrar por estado del proyecto (in_progress, completed, requesting_support).
    - owner_only: Si es True, solo muestra proyectos donde el usuario actual es el iniciador.

    Requiere autenticación JWT.
    """
    try:
        # Obtener organization_id del usuario autenticado
        organization_id = current_user.get("organization_id")

        # Si owner_only es True, filtrar por username del usuario actual
        owner_username = current_user.get("username") if owner_only else None

        projects = await list_projects(
            session=session,
            organization_id=organization_id,
            status=status_filter,
            owner_username=owner_username
        )
        return [ProjectResponse.model_validate(project) for project in projects]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar proyectos: {str(e)}",
        )


@router.get(
    "/by-external-ref/{external_ref}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener proyecto por external_ref",
)
async def get_project_by_external_reference(
    external_ref: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """
    Obtiene un proyecto específico por su external_ref con todas sus etapas del plan de trabajo y observaciones.

    Requiere autenticación JWT.
    """
    try:
        project = await get_project_by_external_ref(external_ref, session)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado",
            )
        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyecto: {str(e)}",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener proyecto por ID",
)
async def get_project(
    project_id: int,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """
    Obtiene un proyecto específico por su ID con todas sus etapas del plan de trabajo.

    Requiere autenticación JWT.
    """
    try:
        project = await get_project_by_id(project_id, session)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado",
            )
        return ProjectResponse.model_validate(project)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyecto: {str(e)}",
        )


@router.get(
    "/collaborations/by-external-ref/{external_ref}",
    response_model=CollaborationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener pedido de colaboración por external_ref",
)
async def get_collaboration_by_external_reference(
    external_ref: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CollaborationRequestResponse:
    """
    Obtiene un pedido de colaboración específico por su external_ref con su etapa asociada.

    Requiere autenticación JWT.
    """
    try:
        collaboration = await get_collaboration_by_external_ref(external_ref, session)
        if not collaboration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido de colaboración no encontrado",
            )
        return CollaborationRequestResponse.model_validate(collaboration)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pedido de colaboración: {str(e)}",
        )


@router.post(
    "/collaborations",
    response_model=CollaborationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pedido de colaboración asociado a un proyecto y una etapa",
)
async def create_stage_collaboration(
    payload: CollaborationRequestCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CollaborationRequestResponse:
    """
    Crea un pedido de colaboración asociado al proyecto y etapa especificados en el body.
    
    El body debe incluir:
    - projectId: ID del proyecto
    - stageId: ID de la etapa
    - title: título del pedido
    - description: descripción (opcional)
    - requestedAmount: monto solicitado (opcional)
    - amountCurrency: moneda del monto (opcional)
    """
    collab = await create_collaboration_request(
        project_id=payload.project_id,
        stage_id=payload.stage_id,
        payload=payload,
        current_user=current_user,
        session=session,
    )
    return CollaborationRequestResponse.model_validate(collab)


@router.get(
    "/{project_id}/collaborations",
    response_model=List[CollaborationRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar pedidos de colaboración de un proyecto",
)
async def get_project_collaborations(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[CollaborationRequestResponse]:
    """
    Recupera todos los pedidos de colaboración asociados al proyecto indicado.
    """
    collaborations = await list_collaboration_requests_by_project(project_id, session)
    # Convertir a Pydantic (Pydantic v2): model_validate desde atributos/ORM
    return [CollaborationRequestResponse.model_validate(c) for c in collaborations]


@router.put(
    "/collaborations/{collaboration_id}/commit",
    response_model=CollaborationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprobar una solicitud de colaboración",
)
async def commit_collaboration(
    collaboration_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CollaborationRequestResponse:
    """
    Aprueba una solicitud de colaboración, cambiando is_approved a true.
    
    Solo el owner del proyecto puede aprobar colaboraciones.
    La colaboración no debe estar completada previamente.
    """
    try:
        collab = await commit_collaboration_request(collaboration_id, current_user, session)
        return CollaborationRequestResponse.model_validate(collab)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aprobar colaboración: {str(e)}",
        )


@router.put(
    "/collaborations/{collaboration_id}/complete",
    response_model=CollaborationRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Marcar como completada una solicitud de colaboración",
)
async def complete_collaboration(
    collaboration_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CollaborationRequestResponse:
    """
    Completa una solicitud de colaboración, cambiando is_completed a true.
    
    Solo el owner del proyecto puede completar colaboraciones.
    La colaboración debe estar previamente aprobada (is_approved = true).
    """
    try:
        collab = await complete_collaboration_request(collaboration_id, current_user, session)
        return CollaborationRequestResponse.model_validate(collab)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar colaboración: {str(e)}",
        )


@router.put(
    "/stages/{stage_id}/complete",
    response_model=WorkPlanStageResponse,
    status_code=status.HTTP_200_OK,
    summary="Marcar como completada una etapa del plan de trabajo",
)
async def complete_stage(
    stage_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> WorkPlanStageResponse:
    """
    Completa una etapa del plan de trabajo, cambiando is_completed a true.
    
    Solo el owner del proyecto puede completar etapas del plan de trabajo.
    """
    try:
        stage = await complete_work_plan_stage(stage_id, current_user, session)
        return WorkPlanStageResponse.model_validate(stage)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar etapa del plan de trabajo: {str(e)}",
        )

@router.get(
    "/observations/by-external-ref/{external_ref}",
    response_model=ObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener observación por external_ref",
)
async def get_observation_by_external_reference(
    external_ref: str,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ObservationResponse:
    """
    Obtiene una observación específica por su external_ref.

    Requiere autenticación JWT.
    """
    try:
        observation = await get_observation_by_external_ref(external_ref, session)
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Observación no encontrada",
            )
        return ObservationResponse.model_validate(observation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener observación: {str(e)}",
        )


@router.post(
    "/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear observacion a un proyecto",
)
async def create_observation(
    payload: ObservationCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ObservationResponse:
    """
    Crea una observacion asociada al proyecto.
    
    El body debe incluir:
    - projectId: ID del proyecto
    - title: título de la observacion
    - description: descripción (opcional)

    """
    try:
        case_id: Optional[int] = None
        task_id: Optional[str] = None

        if settings.use_bonita:
            # Obtener cliente de Bonita y crear caso
            bonita_client = await get_bonita_client(current_user)
            response = await instantiate_observation(bonita_client, payload, current_user["username"])

            # Validar respuesta
            if not response or not response.get("caseId"):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from Bonita: Missing caseId",
                )

            case_id = int(response["caseId"])
            task_id = response.get("taskId")

        # Guardar observacion en la base de datos (con o sin case_id/task_id)
        observation = await save_observation(project_id=payload.project_id, payload=payload, current_user=current_user, session=session, case_id=case_id, task_id=task_id)
        
        return ObservationResponse.model_validate(observation)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
    

@router.get(
    "/{project_id}/observations",
    response_model=List[ObservationResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar observaciones de un proyecto",
)
async def get_project_observations(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[ObservationResponse]:
    """
    Recupera todas las observaciones asociadas al proyecto indicado.
    """
    observations = await list_observation_by_project(project_id, current_user, session)
    # Convertir a Pydantic (Pydantic v2): model_validate desde atributos/ORM
    return [ObservationResponse.model_validate(o) for o in observations]

@router.post(
    "/observations/{observation_id}/resolve",
    response_model=ObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Marcar observación como resuelta",
)
async def resolve_observation(
    observation_id: int,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ObservationResponse:
    """
    Marca una observación como resuelta (is_resolved = true).
    Si USE_BONITA está habilitado y la observación tiene un task_id, completa la tarea en Bonita.
    """
    try:
        bonita_client = None
        if settings.use_bonita:
            bonita_client = await get_bonita_client(current_user)
        
        observation = await resolve_observation_service(observation_id, session, bonita_client)
        return ObservationResponse.model_validate(observation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resolver observación: {str(e)}",
        )