from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Schema para respuesta de información del usuario actual."""
    username: str
    email: Optional[str] = None
    organization_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SetUserOrganizationRequest(BaseModel):
    """Schema para configurar la organización de un usuario."""
    organization_id: int
