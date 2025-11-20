from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, constr


def snake_to_camel(string: str) -> str:
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=snake_to_camel, populate_by_name=True)


class OrganizationBase(CamelCaseModel):
    name: constr(strip_whitespace=True, min_length=3, max_length=150)
    description: Optional[constr(strip_whitespace=True, max_length=500)] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(CamelCaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
