from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Boolean 
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    project_description = Column(String, nullable=True)
    project_category = Column(String, nullable=True)
    requesting_organization = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    estimated_budget = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    priority_level = Column(String, nullable=True)
    supporting_docs_url = Column(String, nullable=True)
    submission_timestamp = Column(DateTime, nullable=True)
    initiator_user_id = Column(String, nullable=True)
    case_id = Column(Integer, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    status = Column(String, default="in_progress", nullable=False)

    # Relationships
    work_plan_stages = relationship("WorkPlanStage", back_populates="project")
    organization = relationship("Organization", back_populates="projects")
    observations = relationship("Observation", back_populates="project", lazy="selectin")

class WorkPlanStage(Base):
    __tablename__ = "work_plan_stages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    stage_name = Column(String, nullable=False)
    stage_start = Column(Date, nullable=True)
    stage_end = Column(Date, nullable=True)
    support_type = Column(String, nullable=True)
    description = Column(String, nullable=True)
    estimated_amount = Column(Float, nullable=True)
    amount_currency = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="work_plan_stages")
    collaboration_requests = relationship("CollaborationRequest", back_populates="stage")

class CollaborationRequest(Base):
    __tablename__ = "collaboration_requests"

    id = Column(Integer, primary_key=True, index=True)
    work_plan_stage_id = Column(Integer, ForeignKey("work_plan_stages.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    requested_amount = Column(Float, nullable=True)
    amount_currency = Column(String, nullable=True)
    requested_date = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    committed_by = Column(String, nullable=False)  # Username from Bonita or local DB

    # Relationships
    stage = relationship("WorkPlanStage", back_populates="collaboration_requests")

class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)  # User ID from Bonita or local DB
    is_resolved = Column(Boolean, default=False)

    # Relationships
    project = relationship("Project", back_populates="observations")