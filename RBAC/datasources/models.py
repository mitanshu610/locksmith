from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from utils.sqlalchemy import Base, TimestampMixin


class DataSourceAccess(TimestampMixin, Base):
    __tablename__ = "datasource_access"

    access_id = Column(UUID(as_uuid=True), primary_key=True)
    datasource_id = Column(BigInteger, index=True)
    user_id = Column(String, nullable=True)
    team_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    org_id = Column(String, nullable=True)
