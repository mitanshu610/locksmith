from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from utils.sqlalchemy import Base, TimestampMixin

class Teams(TimestampMixin, Base):
    __tablename__ = "teams"

    team_id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(String, nullable=False, index=True)
    team_slug = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    name = Column(String, nullable=False)
    created_by = Column(String, nullable=False)


class TeamMemberships(TimestampMixin, Base):
    __tablename__ = "team_memberships"

    membership_id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.team_id", ondelete="CASCADE"), index=True)
    user_id = Column(String, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("team_roles.role_id"))
    removed_at = Column(BigInteger, nullable=True)
    meta_data = Column(JSONB, default=dict)

    __table_args__ = (
        Index('ix_team_memberships_user_id_removed_at', 'user_id', 'removed_at'),
        Index('ix_team_memberships_team_id_removed_at', 'team_id', 'removed_at')
    )