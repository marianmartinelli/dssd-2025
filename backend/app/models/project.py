from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

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

    # Relationships
    work_plan_stages = relationship("WorkPlanStage", back_populates="project")

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

    # Relationships
    project = relationship("Project", back_populates="work_plan_stages")