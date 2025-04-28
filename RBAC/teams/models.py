from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from utils.sqlalchemy import Base, TimestampMixin

class Teams(TimestampMixin, Base):
    __tablename__ = "teams"

    team_id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(String, nullable=False, index=True)
    team_slug = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    created_by = Column(String, nullable=False)


class TeamMemberships(TimestampMixin, Base):
    __tablename__ = "team_memberships"

    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.team_id"), primary_key=True)
    user_id = Column(String, primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("team_roles.role_id"))
    membership_slug = Column(String, unique=True, nullable=True)
    removed_at = Column(BigInteger, nullable=True)
    meta_data = Column(JSONB, default=dict)