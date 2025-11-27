from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, Dict, List
from datetime import date

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.services.metrics_service import (
    get_kpi_metrics,
    get_ong_ranking,
    get_project_status_distribution,
    metric_success_rate,
    metric_late_rate,
    metric_active_projects,
    metric_avg_duration,
    get_demand_supply_analysis,
)
from app.schemas.metrics import KpiData, OngRankingItem, MetricsData
from app.models import CollaborationRequest, Project  # Asegúrate de importar tus modelos

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get(
    "/dashboard",
    response_model=MetricsData,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard metrics"
)
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> MetricsData:
    """
    Devuelve todas las métricas del tablero gerencial.
    Solo accesible para usuarios con rol Rol2.
    """
    #if "Rol2" not in current_user.get("roles", []):
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="Only users with Rol2 can access metrics"
    #    )

    try:
        kpi_result = await get_kpi_metrics(session)
        rankings = await get_ong_ranking(session)
        distributions = await get_project_status_distribution(session)

        # Si el servicio devolvió un dict (resumen) lo colocamos en kpiData
        if isinstance(kpi_result, dict):
            kpis_list: List[KpiData] = []  # opcionalmente construir una lista desde el dict
            kpi_summary: Dict[str, Any] = kpi_result
        else:
            kpis_list = kpi_result
            kpi_summary = None

        return MetricsData(
            kpis=kpis_list,
            ong_ranking=rankings,
            status_distribution=distributions,
            kpiData=kpi_summary,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.get(
    "/kpis",
    response_model=List[KpiData],
    status_code=status.HTTP_200_OK,
    summary="Get KPI metrics"
)
async def get_kpis(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[KpiData]:
    """
    Devuelve los KPIs (Key Performance Indicators) del sistema.
    """
    #if "Rol2" not in current_user.get("roles", []):
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="Only users with Rol2 can access metrics"
    #    )

    return await get_kpi_metrics(session)


@router.get(
    "/ong-ranking",
    response_model=List[OngRankingItem],
    status_code=status.HTTP_200_OK,
    summary="Get ONG ranking"
)
async def get_ong_ranking_endpoint(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> List[OngRankingItem]:
    """
    Devuelve el ranking de ONGs por cantidad de proyectos aprobados.
    """
    #if "Rol2" not in current_user.get("roles", []):
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="Only users with Rol2 can access metrics"
    #    )

    return await get_ong_ranking(session)


#def require_manager(user: dict) -> None:
    #if "Rol2" not in user.get("roles", []):
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Rol2 can access metrics")

# Endpoints globales (sin project_id)

@router.get("/global/success_rate", status_code=status.HTTP_200_OK)
async def get_global_success_rate(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    #require_manager(current_user)
    try:
        stmt = select(func.count(Project.id))
        total_res = await db.execute(stmt)
        total = total_res.scalar() or 0

        if total == 0:
            return {"successRate": 0}

        stmt_completed = select(func.count(CollaborationRequest.id)).where(
            CollaborationRequest.is_completed == True
        )
        comp_res = await db.execute(stmt_completed)
        completed = comp_res.scalar() or 0

        success_rate = int(round((completed / total) * 100))
        return {"successRate": success_rate}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/global/late_rate", status_code=status.HTTP_200_OK)
async def get_global_late_rate(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    #require_manager(current_user)
    try:
        # Aproximación: 100 - successRate
        stmt = select(func.count(CollaborationRequest.id))
        total_res = await db.execute(stmt)
        total = total_res.scalar() or 0

        if total == 0:
            return {"lateRate": 0}

        stmt_completed = select(func.count(CollaborationRequest.id)).where(
            CollaborationRequest.is_completed == True
        )
        comp_res = await db.execute(stmt_completed)
        completed = comp_res.scalar() or 0

        success_rate = int(round((completed / total) * 100))
        late_rate = max(0, 100 - success_rate)
        return {"lateRate": late_rate}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/global/active_projects", status_code=status.HTTP_200_OK)
async def get_global_active_projects(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    #require_manager(current_user)
    try:
        today = date.today()
        stmt = select(func.count(Project.id)).where(
            Project.start_date <= today,
            Project.end_date >= today,
        )
        result = await db.execute(stmt)
        active = result.scalar() or 0
        return {"count": active, "isActive": active > 0}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/global/ong_ranking", status_code=status.HTTP_200_OK)
async def get_global_ong_ranking(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    #require_manager(current_user)
    try:
        stmt = (
            select(
                Project.requesting_organization,
                func.count(Project.id).label("count")
            )
            .group_by(Project.requesting_organization)
            .order_by(func.count(Project.id).desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        rows = result.all()

        ranking = [
            {"ong_name": row[0], "colaboraciones": row[1]}
            for row in rows
        ]
        return {"ranking": ranking}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/global/demand_supply", status_code=status.HTTP_200_OK)
async def get_demand_supply(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Métrica 2: Análisis de Demanda y Oferta.
    Devuelve para cada support_type (demanda) el top 3 de ONGs comprometidas.
    """
    #require_manager(current_user)
    try:
        result = await get_demand_supply_analysis(db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))