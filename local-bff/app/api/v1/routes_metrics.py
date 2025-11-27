from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, Dict, List
from datetime import date, datetime
from structlog import get_logger

from app.api.deps import get_current_user, get_bonita_client
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
from app.services.bonita_client import BonitaClient, get_active_cases
from app.schemas.metrics import KpiData, OngRankingItem, MetricsData
from app.models import CollaborationRequest, Project

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = get_logger()

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
    #if "Gerente" not in user.get("roles", []):
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers (gerente) can access metrics")

# Endpoints globales (sin project_id)

@router.get("/global/success_rate", status_code=status.HTTP_200_OK)
async def get_global_success_rate(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    bonita_client: BonitaClient = Depends(get_bonita_client),
) -> Dict[str, Any]:
    """
    Métrica de Éxito en Plazo para casos ACTIVOS.
    
    1. Obtiene todos los casos activos de Bonita
    2. Busca los case_ids en la BD (Project)
    3. Divide entre: casos en término (end_date > hoy) y casos demorados (end_date <= hoy)
    """
    try:
        # 1. Obtener casos ACTIVOS de Bonita
        active_cases = await get_active_cases(bonita_client)
        
        if not active_cases or len(active_cases) == 0:
            logger.info("No active cases found in Bonita")
            return {
                "successRate": 0,
                "lateRate": 0,
                "total_active": 0,
                "on_time": 0,
                "delayed": 0,
            }
        
        # 2. Extraer los case_ids de Bonita y convertir a integers
        bonita_case_ids = [int(case.get("caseId") or case.get("id")) for case in active_cases]
        bonita_case_ids = [cid for cid in bonita_case_ids if cid]  # filtrar None/0
        
        logger.info("Active cases from Bonita", count=len(bonita_case_ids), case_ids=bonita_case_ids)
        
        if not bonita_case_ids:
            logger.warning("No valid case IDs extracted from Bonita")
            return {
                "successRate": 0,
                "lateRate": 0,
                "total_active": 0,
                "on_time": 0,
                "delayed": 0,
            }
        
        # 3. Consultar PostgreSQL para obtener los proyectos con estos case_ids
        stmt_projects = (
            select(Project.id, Project.case_id, Project.end_date)
            .where(Project.case_id.in_(bonita_case_ids))  # ahora son integers
        )
        db_projects_result = await db.execute(stmt_projects)
        db_projects = db_projects_result.all()
        
        logger.info("Projects found in DB for active cases", count=len(db_projects))
        
        if not db_projects:
            logger.warning("No projects found in DB for active case IDs")
            return {
                "successRate": 0,
                "lateRate": 0,
                "total_active": len(bonita_case_ids),
                "on_time": 0,
                "delayed": 0,
            }
        
        # 4. Clasificar: en término vs demorados
        today = date.today()
        on_time_count = 0
        delayed_count = 0
        
        for project_id, case_id, end_date in db_projects:
            if not end_date:
                # Si no hay fecha de fin, contar como en término (aún activo sin fecha definida)
                on_time_count += 1
                continue
            
            # Si end_date > hoy -> aún en término
            # Si end_date <= hoy -> demorado
            if end_date > today:
                on_time_count += 1
            else:
                delayed_count += 1
        
        total_active = len(db_projects)
        
        # 5. Calcular tasas
        if total_active == 0:
            success_rate = 0
            late_rate = 0
        else:
            success_rate = int(round((on_time_count / total_active) * 100))
            late_rate = int(round((delayed_count / total_active) * 100))
        
        logger.info(
            "Success rate calculation completed",
            total_active=total_active,
            on_time=on_time_count,
            delayed=delayed_count,
            success_rate=success_rate,
            late_rate=late_rate,
        )
        
        return {
            "successRate": success_rate,
            "lateRate": late_rate,
            "total_active": total_active,
            "on_time": on_time_count,
            "delayed": delayed_count,
        }
        
    except ValueError as e:
        logger.error("ValueError in get_global_success_rate", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error in get_global_success_rate", error=str(e))
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