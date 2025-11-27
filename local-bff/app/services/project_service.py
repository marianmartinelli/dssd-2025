from app.schemas.project import ProjectCreate, CollaborationRequestCreate
from typing import Dict, List, Optional
from app.core.database import get_db_session
from app.models.project import Project, WorkPlanStage, CollaborationRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import CollaborationRequest, WorkPlanStage
from datetime import datetime
from fastapi import HTTPException, status

async def save_project(
    payload: ProjectCreate,
    current_user: Dict,
    db_session: AsyncSession,
    case_id: int = None
) -> Project:
    """
    Save the project and its associated plan in the database.

    Args:
        payload (ProjectCreate): The project data sent in the request.
        current_user (Dict): The current authenticated user.
        db_session (AsyncSession): The database session.
        case_id (int, optional): The Bonita case ID if available.

    Returns:
        Project: The saved project with its work plan stages.
    """
    project = Project(
        project_name=payload.project_name,
        project_description=payload.project_description,
        project_category=payload.project_category,
        requesting_organization=payload.requesting_organization,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        estimated_budget=payload.estimated_budget,
        currency=payload.currency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        priority_level=payload.priority_level,
        supporting_docs_url=payload.supporting_docs_url,
        submission_timestamp=datetime.strptime(payload.start_date.strftime("%Y-%m-%dT%H:%M:%S"), "%Y-%m-%dT%H:%M:%S"),
        initiator_user_id=current_user.get("username"),
        case_id=case_id,
        organization_id=current_user.get("organization_id"),
        status="in_progress",
    )
    db_session.add(project)
    await db_session.flush()

    # Save work plan stages
    for stage in payload.work_plan_stages:
        work_plan_stage = WorkPlanStage(
            project_id=project.id,
            stage_name=stage.stage_name,
            stage_start=stage.stage_start,
            stage_end=stage.stage_end,
            support_type=stage.support_type,
            description=stage.description,
            estimated_amount=stage.estimated_amount,
            amount_currency=stage.amount_currency,
        )
        db_session.add(work_plan_stage)

    await db_session.commit()
    await db_session.refresh(project, ["work_plan_stages"])
    return project


async def list_projects(
    session: AsyncSession,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    owner_username: Optional[str] = None
) -> List[Project]:
    """
    List projects with their associated work plan stages, with optional filters.

    Args:
        session (AsyncSession): The database session.
        organization_id (Optional[int]): Filter by organization ID.
        status (Optional[str]): Filter by project status (in_progress, completed, requesting_support).
        owner_username (Optional[str]): Filter by initiator username (owner).

    Returns:
        List[Project]: List of projects matching the filters with their work plan stages.
    """
    stmt = select(Project).options(
        selectinload(Project.work_plan_stages),
        selectinload(Project.observations)
    )

    # Apply filters
    if organization_id is not None:
        stmt = stmt.where(Project.organization_id == organization_id)

    if status is not None:
        stmt = stmt.where(Project.status == status)

    if owner_username is not None:
        stmt = stmt.where(Project.initiator_user_id == owner_username)

    result = await session.execute(stmt)
    projects = result.scalars().all()
    return list(projects)


async def get_project_by_id(project_id: int, session: AsyncSession) -> Optional[Project]:
    """
    Get a specific project by ID with its associated work plan stages.

    Args:
        project_id (int): The ID of the project to retrieve.
        session (AsyncSession): The database session.

    Returns:
        Optional[Project]: The project with its work plan stages, or None if not found.
    """
    stmt = select(Project).where(Project.id == project_id).options(
        selectinload(Project.work_plan_stages),
        selectinload(Project.observations)
    )
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    return project

async def create_collaboration_request(
    project_id: int,
    stage_id: int,
    payload,  # expected to be a Pydantic CollaborationRequestCreate
    current_user: Dict,
    session: AsyncSession,
):
    """
    Create a CollaborationRequest linked to a given project and work plan stage.
    Validates that the stage exists and belongs to the project.
    """
    from app.models.user import User
    
    # Verify stage exists
    stage = await session.get(WorkPlanStage, stage_id)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work plan stage not found")

    # Verify stage belongs to the project
    if stage.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stage does not belong to the specified project",
        )

    # Get project to verify ownership
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Verify that the current user is NOT the project owner
    if project.initiator_user_id == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los owners no pueden crear colaboraciones en sus propios proyectos"
        )

    # Create collaboration request
    collab = CollaborationRequest(
        work_plan_stage_id=stage_id,
        title=payload.title,
        description=payload.description,
        requested_amount=payload.requested_amount,
        amount_currency=payload.amount_currency,
        requested_date=datetime.utcnow(),
        is_approved=False,
        is_completed=False,
        committed_by=current_user["username"],
    )

    try:
        session.add(collab)
        await session.commit()
        await session.refresh(collab)
        return collab
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

async def list_collaboration_requests_by_project(
    project_id: int,
    session: AsyncSession,
) -> List[CollaborationRequest]:
    """
    Devuelve todos los CollaborationRequest asociados a un proyecto.
    Enriquece cada colaboración con el nombre de la organización del usuario que la creó.
    """
    from app.models.user import User
    from sqlalchemy.orm import selectinload

    # Fetch collaboration requests
    stmt = (
        select(CollaborationRequest)
        .join(WorkPlanStage, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
        .where(WorkPlanStage.project_id == project_id)
        .options(selectinload(CollaborationRequest.stage))
    )
    result = await session.execute(stmt)
    collaborations = result.scalars().all()

    # Batch load all users with organizations for efficiency
    usernames = [c.committed_by for c in collaborations]
    if usernames:
        stmt = (
            select(User)
            .where(User.username.in_(usernames))
            .options(selectinload(User.organization))
        )
        result = await session.execute(stmt)
        users_map = {u.username: u for u in result.scalars().all()}
    else:
        users_map = {}

    # Enrich collaborations with organization data
    for collab in collaborations:
        user = users_map.get(collab.committed_by)
        if user and user.organization:
            collab.committed_by_organization = user.organization.name
        else:
            collab.committed_by_organization = "Particular"

    return collaborations


async def commit_collaboration_request(
    collaboration_id: int,
    current_user: Dict,
    session: AsyncSession,
) -> CollaborationRequest:
    """
    Aprueba una solicitud de colaboración (pone is_approved = true).
    Solo el owner del proyecto puede aprobar colaboraciones.
    
    Args:
        collaboration_id (int): ID de la colaboración
        current_user (Dict): Usuario autenticado
        session (AsyncSession): Sesión de BD
        
    Returns:
        CollaborationRequest: La colaboración actualizada
        
    Raises:
        HTTPException: Si la colaboración no existe, ya está completada o el usuario no es el owner
    """
    # Obtener la colaboración con su stage y proyecto
    stmt = (
        select(CollaborationRequest)
        .options(
            selectinload(CollaborationRequest.stage).selectinload(WorkPlanStage.project)
        )
        .where(CollaborationRequest.id == collaboration_id)
    )
    result = await session.execute(stmt)
    collab = result.scalar_one_or_none()
    
    if not collab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de colaboración no encontrada",
        )
    
    # Verificar que el usuario sea el owner del proyecto
    project = collab.stage.project
    if project.initiator_user_id != current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el owner del proyecto puede aprobar colaboraciones",
        )
    
    # Verificar que no esté ya completada
    if collab.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede aprobar una colaboración ya completada",
        )
    
    # Verificar que no esté ya aprobada
    if collab.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La colaboración ya está aprobada",
        )
    
    # Aprobar la colaboración
    collab.is_approved = True
    
    try:
        await session.commit()
        await session.refresh(collab)
        return collab
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


async def complete_collaboration_request(
    collaboration_id: int,
    current_user: Dict,
    session: AsyncSession,
) -> CollaborationRequest:
    """
    Completa una solicitud de colaboración (pone is_completed = true).
    Solo puede completarse si ya está aprobada.
    Solo el owner del proyecto puede completar colaboraciones.
    
    Args:
        collaboration_id (int): ID de la colaboración
        current_user (Dict): Usuario autenticado
        session (AsyncSession): Sesión de BD
        
    Returns:
        CollaborationRequest: La colaboración actualizada
        
    Raises:
        HTTPException: Si la colaboración no existe, no está aprobada, ya está completada o el usuario no es el owner
    """
    # Obtener la colaboración con su stage y proyecto
    stmt = (
        select(CollaborationRequest)
        .options(
            selectinload(CollaborationRequest.stage).selectinload(WorkPlanStage.project)
        )
        .where(CollaborationRequest.id == collaboration_id)
    )
    result = await session.execute(stmt)
    collab = result.scalar_one_or_none()
    
    if not collab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de colaboración no encontrada",
        )
    
    # Verificar que el usuario sea el owner del proyecto
    project = collab.stage.project
    if project.initiator_user_id != current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el owner del proyecto puede completar colaboraciones",
        )
    
    # Verificar que esté aprobada
    if not collab.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden completar colaboraciones previamente aprobadas",
        )
    
    # Verificar que no esté ya completada
    if collab.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La colaboración ya está completada",
        )
    
    # Completar la colaboración
    collab.is_completed = True
    
    try:
        await session.commit()
        await session.refresh(collab)
        return collab
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


async def complete_work_plan_stage(
    stage_id: int,
    current_user: Dict,
    session: AsyncSession,
) -> WorkPlanStage:
    """
    Completa una etapa del plan de trabajo (pone is_completed = true).
    Solo el owner del proyecto puede completar etapas.
    
    Args:
        stage_id (int): ID de la etapa del plan de trabajo
        current_user (Dict): Usuario autenticado
        session (AsyncSession): Sesión de BD
        
    Returns:
        WorkPlanStage: La etapa actualizada
        
    Raises:
        HTTPException: Si la etapa no existe, ya está completada o el usuario no es el owner
    """
    # Obtener la etapa con su proyecto
    stmt = (
        select(WorkPlanStage)
        .options(selectinload(WorkPlanStage.project))
        .where(WorkPlanStage.id == stage_id)
    )
    result = await session.execute(stmt)
    stage = result.scalar_one_or_none()
    
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Etapa del plan de trabajo no encontrada",
        )
    
    # Verificar que el usuario sea el owner del proyecto
    project = stage.project
    if project.initiator_user_id != current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el owner del proyecto puede completar etapas del plan de trabajo",
        )
    
    # Verificar que no esté ya completada
    if stage.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La etapa del plan de trabajo ya está completada",
        )
    
    # Completar la etapa
    stage.is_completed = True
    
    try:
        await session.commit()
        await session.refresh(stage)
        return stage
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))