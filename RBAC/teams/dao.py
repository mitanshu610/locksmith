import time
from uuid import UUID

import uuid6

from sqlalchemy import update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from RBAC.roles.dao import TeamRoleDAO
from RBAC.roles.models import TeamRoles
from RBAC.roles.schemas import TeamRoleEnum
from RBAC.teams.models import Teams, TeamMemberships
from RBAC.teams.exceptions import TeamError, TeamNotFoundError
from RBAC.teams.schemas import TeamUpdateSchema, TeamMemberAddSchema, TeamAddSchema, \
    MemberRoleChangeSchema
from config.logging import logger
from config.settings import loaded_config
from clerk_integration.helpers import ClerkHelper


# --------------- Teams DAO ----------------
class TeamsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_team(self, team_details: TeamAddSchema, user_id: str, org_id: str):
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

    async def get_teams_by_org(self, org_id: str, current_user_id: str):
        try:
            # Get only the teams that the user is a member of in this organization
            user_teams_stmt = (
                select(Teams, TeamMemberships.role_id, TeamRoles.name.label("role_name"), TeamRoles.role_slug)
                .join(
                    TeamMemberships,
                    and_(
                        Teams.team_id == TeamMemberships.team_id,
                        TeamMemberships.user_id == current_user_id,
                        TeamMemberships.removed_at.is_(None)
                    )
                )
                .join(
                    TeamRoles,
                    TeamMemberships.role_id == TeamRoles.role_id
                )
                .where(Teams.org_id == org_id)
            )

            result = await self.session.execute(user_teams_stmt)

            # Build the response with only teams the user is a member of
            teams_with_roles = []
            for row in result:
                team = row.Teams  # Access the Teams object from the row
                team_dict = {
                    "team_id": str(team.team_id),
                    "org_id": team.org_id,
                    "team_slug": team.team_slug,
                    "description": team.description,
                    "name": team.name,
                    "created_by": team.created_by,
                    "user_role": {
                        "role_id": row.role_id,
                        "role_name": row.role_name,
                        "role_slug": row.role_slug
                    }
                }
                teams_with_roles.append(team_dict)

            return teams_with_roles
        except Exception as e:
            logger.error(f"Failed to fetch teams for org {org_id}: {e}")
            raise TeamError(detail=str(e))


    async def get_team_by_id(self, team_id: UUID):
        """Get a team by ID."""
        try:
            stmt = select(Teams).where(Teams.team_id == team_id)
            result = await self.session.execute(stmt)
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError(str(team_id))
            return team
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch team {team_id}: {e}")
            raise TeamError(detail=str(e))


    async def update_team(self, team_id: UUID, team_details: TeamUpdateSchema):
        """Update an existing team."""
        try:
            result = await self.session.execute(select(Teams).where(Teams.team_id == team_id))
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError()

            for key, value in team_details.model_dump(exclude_unset=True).items():
                if value:
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


    async def delete_team(self, team_id: UUID):
        """Delete a team."""
        try:
            result = await self.session.execute(select(Teams).where(Teams.team_id == team_id))
            team = result.scalars().first()
            if not team:
                raise TeamNotFoundError(str(team_id))

            await self.session.delete(team)
            await self.session.commit()
            logger.info(f"Team {str(team_id)} deleted successfully")
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete team {team_id}: {e}")
            raise TeamError("Failed to delete team")


# ---------- Team Membership DAO -------------
class TeamMembershipsDAO:
    def __init__(self, session):
        self.session = session
        self.roles_dao = TeamRoleDAO(session)
        self.clerk_helper = ClerkHelper(loaded_config.clerk_secret_key)

    async def add_member(self, team_id: UUID, member: TeamMemberAddSchema):
        """
        Add one or more members to a team.

        Args:
            team_id: The team to add members to
            member: TeamMemberAddSchema containing one or more user_id/role_id pairs

        Returns:
            Added team memberships
        """
        try:
            results = []
            # Check all members first before adding any
            for user_role in member.members:
                stmt = select(TeamMemberships).where(
                    and_(
                        TeamMemberships.team_id == team_id,
                        TeamMemberships.user_id == user_role.user_id,
                        TeamMemberships.removed_at.is_(None)
                    )
                )
                result = await self.session.execute(stmt)
                existing_member = result.scalar_one_or_none()

                if existing_member:
                    raise TeamError(f"Member with user_id {user_role.user_id} already exists in the team")

            # If we get here, none of the members exist, so we can add them all
            for user_role in member.members:
                role_id = None
                if user_role.role_slug:
                    role_id = await self.roles_dao.get_role_by_slug(user_role.role_slug)
                else:
                    role_id = await self.roles_dao.get_role_by_slug(TeamRoleEnum.MEMBER.value)

                if not role_id:
                    raise TeamError(f"Role not found for slug {user_role.role_slug or 'member'}")

                new_entry = TeamMemberships(
                    membership_id=uuid6.uuid6(),
                    team_id=team_id,
                    user_id=user_role.user_id,
                    role_id=role_id,
                    removed_at=None
                )
                self.session.add(new_entry)
                results.append(new_entry)

            await self.session.commit()

            for entry in results:
                await self.session.refresh(entry)

            logger.info(f"Added {len(results)} members to team {team_id}")

            if len(results) == 1:
                return results[0]
            return results

        except Exception as e:
            await self.session.rollback()  # Add explicit rollback on error
            logger.error(f"Failed to add team member(s): {str(e)}")
            raise TeamError(str(e))  # Pass the original error message

    async def change_member_role(self, member_info: MemberRoleChangeSchema, team_id: UUID):
        try:
            results = {
                "successful": [],
                "failed": []
            }
            for member in member_info.members:
                role_id = await self.roles_dao.get_role_by_slug(member.role_slug)
                if not role_id:
                    raise TeamError("Failed to add member to team: Role slug not found")

                membership_query = select(TeamMemberships).where(
                    and_(
                        TeamMemberships.team_id == team_id,
                        TeamMemberships.user_id == member.user_id,
                        TeamMemberships.removed_at.is_(None)
                    )
                )

                membership_result = await self.session.execute(membership_query)
                existing_membership = membership_result.scalar_one_or_none()
                if not existing_membership:
                    raise TeamError("User/s are not member of this team")

                existing_membership.role_id = role_id
                results["successful"].append({
                    "user_id": member.user_id,
                    "new_role_id": role_id
                })

            await self.session.flush()
            return results
        except Exception as e:
            logger.error(f"Failed to change member role(s): {str(e)}")
            raise TeamError("Failed to change member role(s)")


    async def get_members(self, team_id: UUID, from_clerk=True):
        try:
            user_ids, rows = await self.get_member_user_ids(team_id)

            if not user_ids:
                return []

            clerk_users_by_id = None

            if from_clerk:
                clerk_users_by_id = await self.clerk_helper.get_clerk_users_by_id(user_ids)

            members = []
            for row in rows:
                member_db = row.TeamMemberships
                role_name = row.role_name
                member_dict = {
                    "user_id": member_db.user_id,
                    "team_id": member_db.team_id,
                    "role_id": member_db.role_id,
                    "role_name": role_name
                }
                if from_clerk and clerk_users_by_id:
                    clerk_user = clerk_users_by_id.get(member_db.user_id)
                    member_dict["clerk_user"] = clerk_user


                members.append(member_dict)

            return members

        except Exception as e:
            logger.error("Failed to get members for team %s: %s", str(team_id), str(e))
            raise TeamError("Failed to list team members")


    async def get_member_user_ids(self, team_id: UUID):
        stmt = (
            select(TeamMemberships, TeamRoles.name.label("role_name"))
            .join(TeamRoles, TeamMemberships.role_id == TeamRoles.role_id)
            .where(TeamMemberships.team_id == team_id, TeamMemberships.removed_at.is_(None))
        )
        result = await self.session.execute(stmt)
        rows = result.fetchall()

        user_ids = [row.TeamMemberships.user_id for row in rows]
        return user_ids, rows

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

    async def is_team_owner(self, team_id: UUID, user_id: str):
        """Check if the user has an 'owner' role in the team."""
        owner_role_id = await self.roles_dao.get_role_by_slug(TeamRoleEnum.OWNER.value)

        membership_stmt = select(TeamMemberships).where(
            TeamMemberships.team_id == team_id,
            TeamMemberships.user_id == user_id,
            TeamMemberships.role_id == owner_role_id,
            TeamMemberships.removed_at.is_(None)
        )
        membership_result = await self.session.execute(membership_stmt)
        membership = membership_result.scalar_one_or_none()

        return bool(membership)

    async def get_teams_by_user(self, user_id: str):
        """
        Get all teams that a user belongs to.

        Args:
            user_id (str): The ID of the user

        Returns:
            list: A list of Teams objects that the user is a member of
        """
        try:
            # Join TeamMemberships with Teams to get team details
            stmt = (
                select(Teams)
                .join(TeamMemberships, Teams.team_id == TeamMemberships.team_id)
                .where(
                    TeamMemberships.user_id == user_id,
                    TeamMemberships.removed_at.is_(None)
                )
            )

            result = await self.session.execute(stmt)
            teams = result.scalars().all()

            logger.info(f"Retrieved {len(teams)} teams for user {user_id}")
            return teams

        except Exception as e:
            logger.error(f"Failed to get teams for user {user_id}: {e}")
            raise TeamError(f"Failed to retrieve user's teams: {str(e)}")

    async def get_member_role(self, user_id: str, team_id: UUID):
        try:
            stmt = (
                select(TeamMemberships.role_id)
                .where(
                    TeamMemberships.team_id == team_id,
                    TeamMemberships.user_id == user_id,
                    TeamMemberships.removed_at.is_(None)
                )
            )

            result = await self.session.execute(stmt)
            role_id = result.scalar_one_or_none()

            role_details = await self.roles_dao.get_role_by_id(role_id)

            return role_details
        except Exception as e:
            logger.error(f"Failed to get role for user {user_id}: {e}")
            raise TeamError(f"Failed to retrieve user's role: {str(e)}")
