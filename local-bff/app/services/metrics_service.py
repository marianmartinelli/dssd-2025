from typing import Dict, Any, List
from datetime import date
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, WorkPlanStage, CollaborationRequest
from app.schemas.metrics import OngRankingItem


async def metric_success_rate(project_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    % de collaboration requests del proyecto que están marcadas como completadas.
    """
    # Total de collaboration requests para el proyecto
    stmt_total = (
        select(func.count(CollaborationRequest.id))
        .join(WorkPlanStage, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
        .where(WorkPlanStage.project_id == project_id)
    )
    total_res = await db.execute(stmt_total)
    total = total_res.scalar() or 0

    if total == 0:
        return {"successRate": 0, "total": 0, "completed": 0}

    # Completadas
    stmt_completed = (
        select(func.count(CollaborationRequest.id))
        .join(WorkPlanStage, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
        .where(WorkPlanStage.project_id == project_id)
        .where(CollaborationRequest.is_completed == True)
    )
    comp_res = await db.execute(stmt_completed)
    completed = comp_res.scalar() or 0

    success_rate = int(round((completed / total) * 100))
    return {"successRate": success_rate, "total": total, "completed": completed}


async def metric_late_rate(project_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Tasa aproximada de retraso. Si no hay información de fecha de finalización en la BD,
    se devuelve 100 - successRate como aproximación.
    """
    kpi = await metric_success_rate(project_id, db)
    success = kpi.get("successRate", 0)
    late_rate = max(0, 100 - success)
    return {"lateRate": late_rate, "basedOnSuccessRate": success}


async def metric_active_projects(project_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Determina si el proyecto está activo según start_date/end_date en la BD.
    """
    proj: Project | None = await db.get(Project, project_id)
    if not proj:
        raise ValueError("Project not found")

    today = date.today()
    db_active = bool(proj.start_date and proj.end_date and proj.start_date <= today <= proj.end_date)
    return {"projectId": project_id, "isActive": db_active, "dbStart": proj.start_date, "dbEnd": proj.end_date}


async def metric_avg_duration(project_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Duración promedio por etapa (en días) usando stage_start y stage_end de WorkPlanStage.
    Solo se consideran etapas con ambas fechas.
    """
    stmt = select(WorkPlanStage.stage_start, WorkPlanStage.stage_end).where(WorkPlanStage.project_id == project_id)
    res = await db.execute(stmt)
    rows = res.all()

    durations: List[int] = []
    for (start, end) in rows:
        if start and end:
            delta = (end - start).days
            durations.append(max(0, delta))

    if not durations:
        return {"avgDurationDays": 0, "count": 0}

    avg = int(round(sum(durations) / len(durations)))
    return {"avgDurationDays": avg, "count": len(durations)}

async def get_kpi_metrics(session: AsyncSession) -> Dict[str, Any]:
    """
    Devuelve KPIs compactos usados por el frontend:
      - successRate: % de CollaborationRequest completados
      - lateRate:    100 - successRate (aproximación)
      - activeProjects: cantidad de proyectos cuyo rango incluye la fecha actual
    """
    today = date.today()

    # Total de collaboration requests
    total_stmt = select(func.count(CollaborationRequest.id)).where(
        CollaborationRequest.is_approved == True
    )
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

async def get_demand_supply_analysis(db: AsyncSession) -> Dict[str, Any]:
    """
    Métrica 2: Análisis de Demanda y Oferta
    
    Agrupa collaboration requests por support_type (demanda).
    Para cada tipo, devuelve el top 3 de ONGs que se comprometieron (is_approved=True).
    
    Retorna:
    {
      "demand_supply": [
        {
          "support_type": "Dinero",
          "total_requests": 10,
          "approved_requests": 7,
          "top_3_ongs": [
            {"ong_name": "ONG A", "commitments": 5},
            {"ong_name": "ONG B", "commitments": 2},
            {"ong_name": "ONG C", "commitments": 1}
          ]
        }
      ]
    }
    """
    try:
        # Obtener todos los support_types distintos
        stmt_types = (
            select(
                WorkPlanStage.support_type,
                func.count(WorkPlanStage.id)  
            )
            .distinct() 
            .where(WorkPlanStage.support_type.isnot(None))
            .group_by(WorkPlanStage.support_type)        
            .order_by(desc(func.count(WorkPlanStage.id))) 
            .limit(1)                                    
        )
        result_types = await db.execute(stmt_types)
        support_types = [row[0] for row in result_types.all()]

        demand_supply = []

        for support_type in support_types:
            # Total de pedidos de workplanstages para este support_type
            stmt_total = (
                select(func.count(WorkPlanStage.id))
                .where(WorkPlanStage.support_type == support_type)
            )
            total_res = await db.execute(stmt_total)
            total_requests = total_res.scalar() or 0

            # Requests aprobados (comprometidos)
            stmt_approved = (
                select(func.count(CollaborationRequest.id))
                .join(WorkPlanStage, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
                .where(WorkPlanStage.support_type == support_type)
                .where(CollaborationRequest.is_approved == True)
            )
            approved_res = await db.execute(stmt_approved)
            approved_requests = approved_res.scalar() or 0

            # Top 3 ONGs que se comprometieron (is_approved=True) para este support_type
            stmt_ongs = (
                select(
                    Project.requesting_organization,
                    func.count(CollaborationRequest.id).label("commitment_count")
                )
                .join(WorkPlanStage, Project.id == WorkPlanStage.project_id)
                .join(CollaborationRequest, CollaborationRequest.work_plan_stage_id == WorkPlanStage.id)
                .where(WorkPlanStage.support_type == support_type)
                .where(CollaborationRequest.is_approved == True)
                .group_by(Project.requesting_organization)
                .order_by(func.count(CollaborationRequest.id).desc())
                .limit(3)
            )
            ongs_res = await db.execute(stmt_ongs)
            ongs_rows = ongs_res.all()

            top_3_ongs = [
                {"ong_name": row[0], "commitments": row[1]}
                for row in ongs_rows
            ]

            demand_supply.append({
                "support_type": support_type,
                "total_requests": total_requests,
                "approved_requests": approved_requests,
                "top_3_ongs": top_3_ongs,
            })

        return {"demand_supply": demand_supply}

    except Exception as e:
        raise ValueError(f"Error analyzing demand/supply: {str(e)}")