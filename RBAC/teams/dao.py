import time
from uuid import UUID

import uuid6

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from RBAC.roles.models import TeamRoles
from RBAC.teams.models import Teams, TeamMemberships
from RBAC.teams.exceptions import TeamError, TeamNotFoundError
from RBAC.teams.schemas import TeamCreateSchema, TeamUpdateSchema, TeamMemberAddSchema
from config.logging import logger
from config.settings import loaded_config
from clerk_integration.helpers import ClerkHelper


# --------------- Teams DAO ----------------
class TeamsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_team(self, team_details: TeamCreateSchema, user_id: str, org_id: str):
        """Create a new team."""
        try:
            team_id = uuid6.uuid6()
            team_slug = team_details.team_slug or f"{team_details.name.lower().replace(' ', '-')}-{str(team_id)[:8]}"
            new_team = Teams(
                team_id=team_id,
                org_id=org_id,
                name=team_details.name,
                team_slug=team_slug,
                created_by=user_id
            )
            self.session.add(new_team)
            await self.session.commit()
            await self.session.refresh(new_team)
            logger.info(f"Created new team {new_team.team_slug} with ID {team_id}")
            return new_team
        except IntegrityError as e:
            logger.error(f"Slug or team already exists: {e}")
            raise TeamError("Team slug or name already exists")
        except Exception as e:
            logger.error(f"Failed to create team: {e}")
            raise TeamError(detail=str(e))


    async def get_teams_by_org(self, org_id: str):
        """Get all teams for an org."""
        try:
            stmt = select(Teams).where(Teams.org_id == org_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to fetch teams for org {org_id}: {e}")
            raise TeamError(detail=str(e))


    async def get_team_by_id(self, team_id: str):
        """Get a team by ID."""
        try:
            stmt = select(Teams).where(Teams.team_id == team_id)
            result = await self.session.execute(stmt)
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError(team_id)
            return team
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch team {team_id}: {e}")
            raise TeamError(detail=str(e))


    async def update_team(self, team_id: str, team_details: TeamUpdateSchema):
        """Update an existing team."""
        try:
            result = await self.session.execute(select(Teams).where(Teams.team_id == team_id))
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError(team_id)

            for key, value in team_details.model_dump(exclude_unset=True).items():
                setattr(team, key, value)

            await self.session.commit()
            await self.session.refresh(team)
            logger.info(f"Team {team_id} updated successfully")
            return team
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating team {team_id}: {e}")
            raise TeamError(detail=str(e))


    async def delete_team(self, team_id: str):
        """Delete a team."""
        try:
            result = await self.session.execute(select(Teams).where(Teams.team_id == team_id))
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError(team_id)

            await self.session.delete(team)
            await self.session.commit()
            logger.info(f"Team {team_id} deleted successfully")
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete team {team_id}: {e}")
            raise TeamError("Failed to delete team")


# ---------- Team Membership DAO -------------
class TeamMembershipsDAO:
    def __init__(self, session):
        self.session = session
        self.clerk_helper = ClerkHelper(loaded_config.clerk_secret_key)


    async def add_member(self, team_id: UUID, member: TeamMemberAddSchema):
        try:
            membership_slug = member.membership_slug or f"{str(team_id)[:8]}-{member.user_id[:8]}"
            new_entry = TeamMemberships(
                team_id=team_id,
                user_id=member.user_id,
                role_id=member.role_id,
                membership_slug=membership_slug,
                removed_at=None
            )
            self.session.add(new_entry)
            await self.session.commit()
            await self.session.refresh(new_entry)
            logger.info("Added member %s to team %s", member.user_id, team_id)
            return new_entry
        except Exception as e:
            logger.error("Failed to add team member: %s", str(e))
            raise TeamError("Failed to add member to team")


    async def get_members(self, team_id: str):
        try:
            stmt = (
                select(TeamMemberships, TeamRoles.name.label("role_name"))
                .join(TeamRoles, TeamMemberships.role_id == TeamRoles.role_id)
                .where(TeamMemberships.team_id == team_id, TeamMemberships.removed_at.is_(None))
            )
            result = await self.session.execute(stmt)
            rows = result.fetchall()

            user_ids = [row.TeamMemberships.user_id for row in rows]

            if not user_ids:
                return []

            clerk_users_by_id = await self.clerk_helper.get_clerk_users_by_id(user_ids)

            members = []
            for row in rows:
                member_db = row.TeamMemberships
                role_name = row.role_name
                clerk_user = clerk_users_by_id.get(member_db.user_id)

                member_dict = {
                    "user_id": member_db.user_id,
                    "team_id": member_db.team_id,
                    "role_id": member_db.role_id,
                    "role_name": role_name,
                    "clerk_user": clerk_user
                }
                members.append(member_dict)

            return members

        except Exception as e:
            logger.error("Failed to get members for team %s: %s", str(team_id), str(e))
            raise TeamError("Failed to list team members")


    async def remove_member(self, team_id: UUID, user_id: str):
        try:
            stmt = (
                update(TeamMemberships)
                .where(TeamMemberships.team_id == team_id, TeamMemberships.user_id == user_id)
                .values(removed_at=int(time.time()))
            )
            await self.session.execute(stmt)
            await self.session.commit()
            logger.info("Removed user %s from team %s", user_id, team_id)
        except Exception as e:
            logger.error("Failed to remove member: %s", str(e))
            raise TeamError("Failed to remove team member")


    async def get_team_membership(self, team_id: UUID, user_id: str):
        stmt = (
            select(TeamMemberships, TeamRoles)
            .join(TeamRoles, TeamMemberships.role_id == TeamRoles.role_id)
            .where(
                TeamMemberships.team_id == team_id,
                TeamMemberships.user_id == user_id,
                TeamMemberships.removed_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()

        if not row:
            return None

        membership, role = row
        membership.role = role
        return membership

