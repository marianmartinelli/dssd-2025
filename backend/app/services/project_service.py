from app.schemas.project import ProjectCreate, CollaborationRequestCreate
from typing import Dict, List
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
        initiator_user_id=current_user["username"],
        case_id=case_id,
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


async def list_projects(session: AsyncSession) -> List[Project]:
    """
    List all projects with their associated work plan stages.

    Args:
        session (AsyncSession): The database session.

    Returns:
        List[Project]: List of all projects with their work plan stages.
    """
    stmt = select(Project).options(selectinload(Project.work_plan_stages))
    result = await session.execute(stmt)
    projects = result.scalars().all()
    return list(projects)

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

    # Create collaboration request
    collab = CollaborationRequest(
        work_plan_stage_id=stage_id,
        title=payload.title,
        description=payload.description,
        requested_amount=payload.requested_amount,
        amount_currency=payload.amount_currency,
        requested_date=datetime.utcnow(),
        is_committed=False,
        is_completed=False,
        committed_by=None,
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
    """
    stmt = (
        select(CollaborationRequest)
        .join(WorkPlanStage, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
        .where(WorkPlanStage.project_id == project_id)
        .options(selectinload(CollaborationRequest.stage))
    )
    result = await session.execute(stmt)
    return result.scalars().all()