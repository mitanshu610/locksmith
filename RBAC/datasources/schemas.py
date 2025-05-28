from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class DataSourceSchema(BaseModel):
    type: str = Field(..., description="Type of data source (e.g., 'quip', 'github')")
    config: Dict = Field(..., description="Configuration details for the data source")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "quip",
                "config": {
                    "api_key": "your_api_key",
                    "folder_id": "folder123",
                    "domain": "example.quip.com"
                }
            }
        }


class DataSourceResponseSchema(DataSourceSchema):
    datasource_id: int
    added_by: str
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataSourceAccessSchema(BaseModel):
    datasource_id: int
    user_id: Optional[str] = None
    team_id: Optional[UUID] = None
    org_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DataSourceAccessResponseSchema(DataSourceAccessSchema):
    model_config = ConfigDict(from_attributes=True)


class RevokeAccessSchema(BaseModel):
    datasource_id: int
    user_id: Optional[str] = None
    team_id: Optional[UUID] = None
    org_id: Optional[str] = None