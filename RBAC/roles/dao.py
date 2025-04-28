import uuid6
from sqlalchemy import select

from RBAC.roles.models import TeamRoles
from RBAC.roles.schemas import TeamRoleSchema
from config.logging import logger


class TeamRoleDAO:
    def __init__(self, session):
        self.session = session

    async def create_role(self, role: TeamRoleSchema):
        role_id = uuid6.uuid6()
        new_role = TeamRoles(
            role_id=role_id,
            name=role.name,
            description=role.description,
            role_slug=role.slug
        )
        self.session.add(new_role)
        await self.session.commit()
        await self.session.refresh(new_role)
        logger.info("Created new team role %s", role.name)
        return new_role

    async def get_role_by_slug(self, slug: str) -> TeamRoles | None:
        stmt = select(TeamRoles).where(TeamRoles.role_slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> list[TeamRoles]:
        stmt = select(TeamRoles)
        result = await self.session.execute(stmt)
        return result.scalars().all()