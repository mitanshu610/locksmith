from sqlalchemy.exc import SQLAlchemyError

from RBAC.roles.dao import TeamRoleDAO
from RBAC.roles.schemas import TeamRoleSchema
from RBAC.teams.exceptions import TeamError
from utils.connection_handler import ConnectionHandler
from config.logging import logger


class TeamRoleService:
    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.session = connection_handler.session if connection_handler else None
        self.dao = TeamRoleDAO(self.session)

    async def create_role(self, role: TeamRoleSchema):
        try:
            return await self.dao.create_role(role)
        except SQLAlchemyError as e:
            if self.session:
                await self.session.rollback()
            logger.error("Database error creating team role: %s", str(e))
            raise TeamError("Failed to create team role")
        except Exception as e:
            if self.session:
                await self.session.rollback()
            logger.error("Error creating team role: %s", str(e))
            raise

    async def get_all_roles(self):
        try:
            return await self.dao.get_all_roles()
        except SQLAlchemyError as e:
            logger.error("Database error fetching team roles: %s", str(e))
            raise TeamError("Failed to fetch team roles")