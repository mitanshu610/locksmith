import re
from typing import Optional

from enum import Enum

from pydantic import BaseModel, Field, model_validator, ConfigDict


# ---------- Team Roles ----------
class TeamRoleSchema(BaseModel):
    name: str = Field(..., description="Role name (e.g., manager, member)")
    description: Optional[str] = Field(None, description="Role description")
    slug: Optional[str] = Field(None, description="Auto-generated slug for the role")

    @model_validator(mode="after")
    def generate_slug(self):
        if not self.slug:
            self.slug = re.sub(r'\s+', '-', self.name.strip().lower())
        return self

    model_config = ConfigDict(from_attributes=True)


class TeamRoleEnum(str, Enum):
    """Enumeration for Team Roles."""

    OWNER = "owner"
    MEMBER = "member"