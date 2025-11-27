from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class KpiData(BaseModel):
    title: str
    value: int | str | float
    icon: str
    description: str

class OngRankingItem(BaseModel):
    rank: int
    ong_name: str
    projects_count: int

class MetricsData(BaseModel):
    kpis: List[KpiData]
    ong_ranking: List[OngRankingItem]
    status_distribution: dict

    # Nuevo: resumen compacto de KPIs que usa el frontend (successRate, lateRate, activeProjects)
    kpiData: Optional[Dict[str, Any]] = None

class BonitaCompletedCase(BaseModel):
    """Representa un case completado en Bonita con caseId y endDate."""
    caseId: int
    endDate: Optional[datetime] = None

    class Config:
        from_attributes = True