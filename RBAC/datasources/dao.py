from typing import Optional
from uuid import UUID

import uuid6
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from RBAC.datasources.models import DataSourceAccess
from RBAC.datasources.schemas import DataSourceAccessSchema

class DataSourceAccessDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_access(self, payload: DataSourceAccessSchema):
        # Check if access already exists for this specific combination
        query = select(DataSourceAccess).where(
            DataSourceAccess.datasource_id == payload.datasource_id
        )

        # Add filters for the provided identifiers
        if payload.user_id:
            query = query.where(DataSourceAccess.user_id == payload.user_id)
        if payload.team_id:
            query = query.where(DataSourceAccess.team_id == payload.team_id)
        if payload.org_id:
            query = query.where(DataSourceAccess.org_id == payload.org_id)

        existing_access = await self.session.execute(query)
        existing_access = existing_access.scalars().first()

        if existing_access:
            for key, value in payload.model_dump().items():
                setattr(existing_access, key, value)
            await self.session.commit()
            await self.session.refresh(existing_access)
            return existing_access
        else:
            new_access = DataSourceAccess(
                access_id=uuid6.uuid6(),
                **payload.model_dump()
            )
            self.session.add(new_access)
            await self.session.commit()
            await self.session.refresh(new_access)
            return new_access

    async def delete_access(self, datasource_id):
        await self.session.execute(
            delete(DataSourceAccess).where(DataSourceAccess.datasource_id == datasource_id)
        )
        await self.session.commit()

    async def get_by_user(self, user_id: str):
        stmt = select(DataSourceAccess).where(DataSourceAccess.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_team(self, team_id: UUID):
        stmt = select(DataSourceAccess).where(DataSourceAccess.team_id == team_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_org(self, org_id: str):
        stmt = select(DataSourceAccess).where(DataSourceAccess.org_id == org_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_datasource(self, datasource_id):
        stmt = select(DataSourceAccess).where(DataSourceAccess.datasource_id == datasource_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def check_access(self, datasource_id, user_id, team_id, org_id) -> bool:
        stmt = select(DataSourceAccess).where(
            DataSourceAccess.datasource_id == datasource_id,
            (DataSourceAccess.user_id == user_id) |
            (DataSourceAccess.team_id == team_id) |
            (DataSourceAccess.org_id == org_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None


    async def get_users_with_access_status(self, datasource_id: int, organization_id: Optional[str] = None):
        """
        Get all users in an organization with their access status to a datasource:
        - Direct access (user_id explicitly granted)
        - Team access (member of a team with access)
        - Organization access (member of an organization with access)
        - No access

        Args:
            datasource_id (int): ID of the datasource
            organization_id (str): ID of the organization

        Returns:
            dict: User IDs mapped to their access types
        """
        # Get all access records for this datasource
        stmt = select(DataSourceAccess).where(
            DataSourceAccess.datasource_id == datasource_id
        )
        result = await self.session.execute(stmt)
        access_records = result.scalars().all()

        # Categorize access
        direct_user_access = [record.user_id for record in access_records if record.user_id is not None]
        team_access = [str(record.team_id) for record in access_records if record.team_id is not None]
        org_access = [record.org_id for record in access_records if record.org_id is not None]

        # Check if organization has direct access
        access_result = {
            "direct_user_access": direct_user_access,
            "team_access": team_access,
            "org_access": org_access,
        }
        if organization_id:
            org_has_access = organization_id in org_access
            access_result["org_has_access"] = org_has_access

        return access_result

    async def delete_specific_access(self, datasource_id, user_id=None, team_id=None, org_id=None):
        """
        Delete a specific access record based on the combination of identifiers provided.
        At least one of user_id, team_id, or org_id must be provided.

        Args:
            datasource_id: The ID of the datasource
            user_id: Optional user ID to filter by
            team_id: Optional team ID to filter by
            org_id: Optional organization ID to filter by

        Returns:
            bool: True if an access record was deleted, False otherwise
        """
        query = delete(DataSourceAccess).where(
            DataSourceAccess.datasource_id == datasource_id
        )

        if user_id:
            query = query.where(DataSourceAccess.user_id == user_id)
        if team_id:
            query = query.where(DataSourceAccess.team_id == team_id)
        if org_id:
            query = query.where(DataSourceAccess.org_id == org_id)

        await self.session.execute(query)
        await self.session.commit()

    async def get_all_entities_with_access(self, datasource_id: int):
        """
        Get all entities (users, teams, organizations) that have access to a specific datasource.

        Args:
            datasource_id (int): The ID of the datasource

        Returns:
            dict: A dictionary containing lists of user_ids, team_ids, and org_ids
                  with access to the datasource
        """
        # Query all access records for this datasource
        stmt = select(DataSourceAccess).where(DataSourceAccess.datasource_id == datasource_id)
        result = await self.session.execute(stmt)
        access_records = result.scalars().all()

        # Extract the entities with access
        user_ids = [record.user_id for record in access_records if record.user_id is not None]
        team_ids = [record.team_id for record in access_records if record.team_id is not None]
        org_ids = [record.org_id for record in access_records if record.org_id is not None]

        return {
            "user_ids": user_ids,
            "team_ids": team_ids,
            "org_ids": org_ids
        }