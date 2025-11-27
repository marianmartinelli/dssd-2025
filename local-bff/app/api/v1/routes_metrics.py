from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.services.metrics_service import (
    get_kpi_metrics,
    get_ong_ranking,
    get_project_status_distribution,
)
from app.schemas.metrics import KpiData, OngRankingItem, MetricsData

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