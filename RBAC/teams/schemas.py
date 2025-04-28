# ---------- Team ----------
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TeamCreateSchema(BaseModel):
    name: str = Field(..., description="Name of the team")
    team_slug: Optional[str] = Field(None, description="Slug for the team")
    created_by: Optional[str] = Field(None, description="Clerk user ID who created the team")

    model_config = ConfigDict(from_attributes=True)


class TeamGetSchema(TeamCreateSchema):
    team_id: UUID

    model_config = ConfigDict(from_attributes=True)


class TeamUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Updated team name")
    team_slug: Optional[str] = Field(None, description="Updated team slug")


# ---------- Team Members ----------
class TeamMemberAddSchema(BaseModel):
    user_id: str = Field(..., description="Clerk user ID")
    role_id: UUID = Field(..., description="Role ID assigned to the user")
    membership_slug: Optional[str] = Field(None, description="Slug for the membership")

    model_config = ConfigDict(from_attributes=True)


class OrgMembersQueryParams(BaseModel):
    query: Optional[str] = Field(None, description="Search query for filtering members")
    limit: Optional[int] = Field(10, description="Maximum number of results to return", ge=1)
    offset: Optional[int] = Field(0, description="Number of results to skip", ge=0)
    team_id: Optional[UUID] = Field(..., description="Team for which we have to show members")

    @field_validator('limit')
    def validate_limit(cls, v):
        if v is not None and v > 100:
            return 100
        return v