from uuid import UUID

import uuid6
from sqlalchemy import select

from RBAC.roles.models import TeamRoles
from RBAC.roles.schemas import TeamRoleSchema
from config.logging import logger
from config.settings import loaded_config


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
        if loaded_config.all_roles_data:
            return loaded_config.all_roles_data[slug]
        stmt = select(TeamRoles).where(TeamRoles.role_slug == slug)
        query_result = await self.session.execute(stmt)
        result = query_result.scalar_one_or_none()
        if result:
            return result.role_id
        return result

    async def get_all_roles(self) -> list[TeamRoles]:
        stmt = select(TeamRoles)
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_role_by_id(self, role_id: UUID) -> TeamRoles | None:
        stmt = select(TeamRoles).where(TeamRoles.role_id == role_id)
        query_result = await self.session.execute(stmt)
        result = query_result.scalar_one_or_none()
        return result