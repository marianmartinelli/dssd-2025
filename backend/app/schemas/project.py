from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, constr


SupportType = Literal["financial", "materials", "labor", "logistics", "other"]
PriorityLevel = Literal["low", "medium", "high", "critical"]


class WorkPlanStage(BaseModel):
    stage_name: constr(strip_whitespace=True, min_length=3, max_length=120)
    stage_start: date
    stage_end: date
    support_type: SupportType
    description: constr(strip_whitespace=True, min_length=5, max_length=500)
    estimated_amount: Optional[float] = Field(None, ge=0)
    amount_currency: Optional[str] = Field(None, min_length=3, max_length=3)


class ProjectBase(BaseModel):
    project_name: constr(strip_whitespace=True, min_length=5, max_length=150)
    project_description: constr(strip_whitespace=True, min_length=20, max_length=2000)
    project_category: constr(strip_whitespace=True, min_length=3, max_length=80)
    requesting_organization: constr(strip_whitespace=True, min_length=3, max_length=120)
    contact_email: constr(strip_whitespace=True, min_length=5, max_length=120)
    contact_phone: Optional[constr(strip_whitespace=True, min_length=6, max_length=30)]
    estimated_budget: float = Field(ge=0)
    currency: constr(strip_whitespace=True, min_length=3, max_length=3)
    start_date: date
    end_date: date
    priority_level: PriorityLevel
    supporting_docs_url: Optional[str]


class ProjectCreate(ProjectBase):
    work_plan_stages: List[WorkPlanStage] = Field(..., min_length=1, max_length=20)


class BonitaInstantiationResult(BaseModel):
    case_id: int
    process_definition_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
