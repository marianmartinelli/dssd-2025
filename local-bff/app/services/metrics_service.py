from sqlalchemy import select, func
from datetime import date
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, CollaborationRequest, WorkPlanStage
from app.schemas.metrics import KpiData, OngRankingItem

async def get_kpi_metrics(session: AsyncSession) -> Dict[str, Any]:
    """
    Devuelve KPIs compactos usados por el frontend:
      - successRate: % de CollaborationRequest completados
      - lateRate:    100 - successRate (aproximación)
      - activeProjects: cantidad de proyectos cuyo rango incluye la fecha actual
    """
    today = date.today()

    # Total de collaboration requests
    total_stmt = select(func.count(CollaborationRequest.id))
    total_res = await session.execute(total_stmt)
    total_requests = total_res.scalar() or 0

    # Completados
    completed_stmt = select(func.count(CollaborationRequest.id)).where(
        CollaborationRequest.is_completed == True
    )
    completed_res = await session.execute(completed_stmt)
    completed_requests = completed_res.scalar() or 0

    # Success rate (porcentaje entero)
    success_rate = int(round((completed_requests / total_requests) * 100)) if total_requests else 0

    # Late rate: como aproximación usamos 100 - success_rate (puedes refinar si dispones de fecha de finalización)
    late_rate = max(0, 100 - success_rate)

    # Proyectos activos: aquellos cuyo start_date <= hoy <= end_date
    active_stmt = select(func.count(Project.id)).where(
        Project.start_date <= today,
        Project.end_date >= today,
    )
    active_res = await session.execute(active_stmt)
    active_projects = active_res.scalar() or 0

    return {
        "successRate": success_rate,
        "lateRate": late_rate,
        "activeProjects": active_projects,
    }


async def get_ong_ranking(session: AsyncSession) -> List[OngRankingItem]:
    """
    Devuelve el ranking de ONGs por cantidad de proyectos aprobados.
    """
    stmt = (
        select(
            Project.requesting_organization,
            func.count(Project.id).label("project_count")
        )
        .group_by(Project.requesting_organization)
        .order_by(func.count(Project.id).desc())
        .limit(10)
    )
    
    result = await session.execute(stmt)
    rows = result.all()

    return [
        OngRankingItem(
            rank=idx + 1,
            ong_name=row[0],
            projects_count=row[1],
        )
        for idx, row in enumerate(rows)
    ]


async def get_project_status_distribution(session: AsyncSession) -> dict:
    """
    Devuelve la distribución de proyectos por estado/categoría.
    """
    stmt = (
        select(
            Project.project_category,
            func.count(Project.id).label("count")
        )
        .group_by(Project.project_category)
    )
    
    result = await session.execute(stmt)
    rows = result.all()

    return {
        "categories": [row[0] for row in rows],
        "counts": [row[1] for row in rows],
    }