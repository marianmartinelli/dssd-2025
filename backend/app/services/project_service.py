from app.schemas.project import ProjectCreate
from typing import Dict, List
from app.core.database import get_db_session
from app.models.project import Project, WorkPlanStage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

async def save_project(payload: ProjectCreate, bonita_response: Dict, current_user: Dict):
    """
    Save the project and its associated plan in the database.

    Args:
        payload (ProjectCreate): The project data sent in the request.
        bonita_response (Dict): The response from Bonita containing case and process IDs.
        current_user (Dict): The current authenticated user.

    Returns:
        None
    """
    session_generator = get_db_session()
    session = await session_generator.__anext__()
    try:
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
        )
        session.add(project)
        await session.flush() 

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
            session.add(work_plan_stage)

        await session.commit()
    finally:
        await session.close()


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