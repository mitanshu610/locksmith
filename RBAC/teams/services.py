from uuid import UUID

from clerk_integration.helpers import ClerkHelper
from clerk_integration.utils import UserData
from fastapi import HTTPException, status

from RBAC.roles.dao import TeamRoleDAO
from RBAC.roles.schemas import TeamRoleEnum
from RBAC.teams.dao import TeamsDAO, TeamMembershipsDAO
from RBAC.teams.exceptions import TeamNotFoundError, TeamError
from config.logging import logger
from config.settings import loaded_config
from utils.connection_handler import ConnectionHandler
from RBAC.teams.schemas import TeamCreateSchema, TeamUpdateSchema, TeamMemberAddSchema, OrgMembersQueryParams


# ------- Teams service --------
class TeamService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.teams_dao = TeamsDAO(session=connection_handler.session)
        self.memberships_dao = TeamMembershipsDAO(session=connection_handler.session)
        self.roles_dao = TeamRoleDAO(session=connection_handler.session)

    async def create_team(self, team_details: TeamCreateSchema, user_id: str, org_id: str):
        try:
            # Start transaction
            team = await self.teams_dao.create_team(team_details, user_id, org_id)

            owner_role = await self.roles_dao.get_role_by_slug(TeamRoleEnum.OWNER.value)
            if not owner_role:
                await self.connection_handler.session.rollback()
                raise ValueError("Owner role not found")

            await self.memberships_dao.add_member(
                team_id=str(team.team_id),
                member=TeamMemberAddSchema(
                    user_id=user_id,
                    role_id=owner_role.role_id,
                    membership_slug=None
                )
            )

            # Commit the transaction
            await self.connection_handler.session.commit()
            return TeamCreateSchema.model_validate(team)
        except (TeamError, ValueError) as e:
            await self.connection_handler.session.rollback()
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Unexpected error creating team: {e}")
            raise TeamError(f"Failed to create team: {str(e)}")

    async def get_teams_by_org(self, org_id: str):
        try:
            return await self.teams_dao.get_teams_by_org(org_id)
        except Exception as e:
            logger.error(f"Error fetching teams for org {org_id}: {e}")
            raise TeamError(f"Failed to fetch teams: {str(e)}")

    async def get_team_by_id(self, team_id: str):
        try:
            return await self.teams_dao.get_team_by_id(team_id)
        except TeamNotFoundError:
            # Pass through expected errors
            raise
        except Exception as e:
            logger.error(f"Error fetching team {team_id}: {e}")
            raise TeamError(f"Failed to fetch team: {str(e)}")

    async def update_team(self, team_id: str, team_details: TeamUpdateSchema):
        try:
            team = await self.teams_dao.update_team(team_id, team_details)
            await self.connection_handler.session.commit()
            return team
        except TeamNotFoundError:
            # Pass through expected errors
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Error updating team {team_id}: {e}")
            raise TeamError(f"Failed to update team: {str(e)}")

    async def delete_team(self, team_id: str):
        try:
            await self.teams_dao.delete_team(team_id)
            await self.connection_handler.session.commit()
            return True
        except TeamNotFoundError:
            # Pass through expected errors
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Error deleting team {team_id}: {e}")
            raise TeamError(f"Failed to delete team: {str(e)}")


# ------- Team membership service --------
class TeamMembershipService:
    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.memberships_dao = TeamMembershipsDAO(connection_handler.session)
        self.clerk_helper = ClerkHelper(loaded_config.clerk_secret_key)

    async def _assert_owner(self, team_id: UUID, user_id: str):
        """Ensure the user is an OWNER of the team."""
        member = await self.memberships_dao.get_team_membership(team_id, user_id)
        if not member or member.role.role_slug != TeamRoleEnum.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only team owner can perform this action."
            )

    async def add_member(self, team_id: UUID, member: TeamMemberAddSchema, performed_by: str):
        try:
            await self._assert_owner(team_id, performed_by)
            result = await self.memberships_dao.add_member(team_id, member)
            await self.connection_handler.session.commit()
            return result
        except HTTPException:
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Failed to add member: {e}")
            raise TeamError("Failed to add member to team")

    async def get_members(self, team_id: str):
        try:
            return await self.memberships_dao.get_members(team_id)
        except Exception as e:
            logger.error(f"Failed to get members for team {team_id}: {e}")
            raise TeamError("Failed to list team members")

    async def remove_member(self, team_id: UUID, user_id: str, performed_by: str):
        try:
            await self._assert_owner(team_id, performed_by)
            await self.memberships_dao.remove_member(team_id, user_id)
            await self.connection_handler.session.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Failed to remove member: {e}")
            raise TeamError("Failed to remove team member")

    async def get_org_members(self, query_params: OrgMembersQueryParams, user_data: UserData):
        try:
            await self._assert_owner(query_params.team_id, user_data.userId)
            org_members = await self.clerk_helper.get_org_members(
                user_data.orgId,
                query_params.query,
                query_params.limit,
                query_params.offset
            )

            return org_members
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to remove member: {e}")
            raise TeamError("Failed to get org members")