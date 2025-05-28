from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from utils.sqlalchemy import Base, TimestampMixin


class TeamRoles(TimestampMixin, Base):
    __tablename__ = "team_roles"

    role_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    role_slug = Column(String, unique=True, nullable=False)
