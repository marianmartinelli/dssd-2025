from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, constr


def snake_to_camel(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=snake_to_camel, populate_by_name=True)


SupportType = Literal["financial", "materials", "labor", "logistics", "other"]
PriorityLevel = Literal["low", "medium", "high", "critical"]
ProjectStatus = Literal["in_progress", "completed", "requesting_support"]


class WorkPlanStage(CamelCaseModel):
    stage_name: constr(strip_whitespace=True, min_length=3, max_length=120)
    stage_start: date
    stage_end: date
    support_type: SupportType
    description: constr(strip_whitespace=True, min_length=5, max_length=500)
    estimated_amount: Optional[float] = Field(None, ge=0)
    amount_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    external_ref: Optional[str] = None


class ProjectBase(CamelCaseModel):
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
    supporting_docs_url: Optional[str] = None
    external_ref: Optional[str] = None


class ProjectCreate(ProjectBase):
    work_plan_stages: List[WorkPlanStage] = Field(..., min_length=1, max_length=20)


class BonitaInstantiationResult(CamelCaseModel):
    case_id: int
    process_definition_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkPlanStageResponse(CamelCaseModel):
    id: int
    external_ref: Optional[str] = None
    project_id: int
    stage_name: str
    stage_start: Optional[date] = None
    stage_end: Optional[date] = None
    support_type: Optional[str] = None
    description: Optional[str] = None
    estimated_amount: Optional[float] = None
    amount_currency: Optional[str] = None
    is_completed: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(CamelCaseModel):
    id: int
    external_ref: Optional[str] = None
    project_name: str
    project_description: Optional[str] = None
    project_category: Optional[str] = None
    requesting_organization: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    estimated_budget: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority_level: Optional[str] = None
    supporting_docs_url: Optional[str] = None
    submission_timestamp: Optional[datetime] = None
    initiator_user_id: Optional[str] = None
    case_id: Optional[int] = None
    organization_id: Optional[int] = None
    status: str = "in_progress"
    work_plan_stages: List[WorkPlanStageResponse] = []
    observations: List['ObservationResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class CollaborationRequestCreate(CamelCaseModel):
    project_id: int
    stage_id: int
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    requested_amount: Optional[float] = Field(None, ge=0)
    amount_currency: Optional[str] = Field(None, max_length=3)
    external_ref: Optional[str] = None


class CollaborationRequestResponse(CamelCaseModel):
    id: int
    external_ref: Optional[str] = None
    stage_id: int = Field(alias="work_plan_stage_id")
    title: str
    description: Optional[str] = None
    requested_amount: Optional[float] = None
    amount_currency: Optional[str] = None
    requested_date: Optional[datetime] = None
    is_approved: Optional[bool] = False
    is_completed: Optional[bool] = False
    committed_by: str
    committed_by_organization: Optional[str] = "Particular"

    model_config = ConfigDict(from_attributes=True)


class ObservationCreate(CamelCaseModel):
    project_id: int
    title: constr(strip_whitespace=True, min_length=3, max_length=150)
    description: Optional[constr(strip_whitespace=True, min_length=5, max_length=1000)] = None
    external_ref: Optional[str] = None


class ObservationResponse(CamelCaseModel):
    id: int
    external_ref: Optional[str] = None
    project_id: int
    title: str
    description: Optional[str] = None
    created_date: Optional[datetime] = None
    created_by: str
    is_resolved: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)
