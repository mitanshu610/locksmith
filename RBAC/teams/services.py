from uuid import UUID
from collections import defaultdict

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
from RBAC.teams.schemas import TeamCreateSchema, TeamUpdateSchema, TeamMemberAddSchema, OrgMembersQueryParams, \
    UserRolePair, TeamAddSchema, MemberRoleChangeSchema


# ------- Teams service --------
class TeamService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.teams_dao = TeamsDAO(session=connection_handler.session)
        self.memberships_dao = TeamMembershipsDAO(session=connection_handler.session)
        self.roles_dao = TeamRoleDAO(session=connection_handler.session)

    async def create_team(self, team_details: TeamAddSchema, user_id: str, org_id: str):
        try:
            team = await self.teams_dao.create_team(team_details, user_id, org_id)
            user_role_pair = UserRolePair(user_id=user_id, role_slug=TeamRoleEnum.OWNER.value)
            member_schema = TeamMemberAddSchema(
                members=[user_role_pair]
            )

            await self.memberships_dao.add_member(
                team_id=team.team_id,
                member=member_schema
            )
            await self.connection_handler.session.commit()
            return TeamCreateSchema.model_validate(team)
        except (TeamError, ValueError) as e:
            await self.connection_handler.session.rollback()
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Unexpected error creating team: {e}")
            raise TeamError(f"Failed to create team: {str(e)}")

    async def get_teams_by_user_org(self, org_id: str, user_id: str):
        try:
            return await self.teams_dao.get_teams_by_org(org_id, user_id)
        except Exception as e:
            logger.error(f"Error fetching teams for org {org_id}: {e}")
            raise TeamError(f"Failed to fetch teams: {str(e)}")

    async def get_team_by_id(self, team_id: UUID, user_data: UserData):
        try:
            user_role = await self.memberships_dao.get_member_role(user_data.userId, team_id)
            team_details = await self.teams_dao.get_team_by_id(team_id)
            return {
                "team_id": team_details.team_id,
                "name": team_details.name,
                "description": team_details.description,
                "team_slug": team_details.team_slug,
                "created_by": team_details.created_by,
                "user_role": {
                    "role_id": user_role.role_id,
                    "role_slug": user_role.role_slug,
                    "role_name": user_role.name
                }
            }
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching team {team_id}: {e}")
            raise TeamError(f"Failed to fetch team: {str(e)}")

    async def update_team(self, team_id: UUID, team_details: TeamUpdateSchema):
        try:
            team = await self.teams_dao.update_team(team_id, team_details)
            await self.connection_handler.session.commit()
            return team
        except TeamNotFoundError:
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Error updating team {team_id}: {e}")
            raise TeamError(f"Failed to update team: {str(e)}")

    async def delete_team(self, team_id: UUID):
        try:
            await self.teams_dao.delete_team(team_id)
            await self.connection_handler.session.commit()
            return True
        except TeamNotFoundError:
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
        self.teams_dao = TeamsDAO(connection_handler.session)
        self.roles_dao = TeamRoleDAO(connection_handler.session)

    async def _assert_owner(self, team_id: UUID, user_id: str):
        """Ensure the user is an OWNER of the team."""
        is_owner = await self.memberships_dao.is_team_owner(team_id, user_id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only team owner can perform this action."
            )

    async def add_member(self, team_id: UUID, member: TeamMemberAddSchema, performed_by: str):
        """
        Add one or more members to a team.

        Args:
            team_id: UUID of the team
            member: TeamMemberAddSchema with one or more members to add
            performed_by: User ID of the user performing the action

        Returns:
            Added team memberships
        """
        try:
            await self._assert_owner(team_id, performed_by)
            result = await self.memberships_dao.add_member(team_id, member)
            await self.connection_handler.session.commit()
            return result
        except HTTPException:
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error(f"Failed to add member(s): {e}")
            raise TeamError("Failed to add member(s) to team")

    async def get_members(self, team_id: UUID):
        try:
            return await self.memberships_dao.get_members(team_id)
        except Exception as e:
            logger.error(f"Failed to get members for team {team_id}: {e}")
            raise TeamError("Failed to list team members")

    async def remove_member(self, team_id: UUID, user_id: str, performed_by: str):
        try:
            if performed_by == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot remove yourself from the team."
                )
            await self._assert_owner(team_id, performed_by)
            team_members = await self.memberships_dao.get_members(team_id, from_clerk=False)
            if len(team_members) == 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Empty team cannot exist kindly delete the team."
                )
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
            query = query_params.query if query_params.query and len(query_params.query) else None
            if not user_data.orgId:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No active organisation provided."
                )

            org_members = await self.clerk_helper.get_org_members(
                user_data.orgId,
                query,
                query_params.limit,
                query_params.offset
            )

            existing_team_member_ids, _ = await self.memberships_dao.get_member_user_ids(team_id=query_params.team_id)

            filtered_org_members = defaultdict(list)
            for member in org_members["members"]:
                if member['id'] not in existing_team_member_ids:
                    filtered_org_members["members"].append(member)

            return filtered_org_members
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to remove member: {e}")
            raise TeamError("Failed to get org members")

    async def change_members_role(self, member_info: MemberRoleChangeSchema, user_data: UserData, team_id: UUID):
        try:
            await self._assert_owner(team_id, user_data.userId)
            team_members = await self.memberships_dao.get_members(team_id=team_id, from_clerk=False)
            if len(team_members) == 1 and team_members[0]["role_id"] == loaded_config.all_roles_data[TeamRoleEnum.OWNER.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="There should be at least one owner of the team."
                )
            data = await self.memberships_dao.change_member_role(member_info, team_id)
            await self.connection_handler.session.commit()  # Make sure this is awaited if it's an async function
            return data
        except HTTPException:
            raise
        except Exception as e:
            await self.connection_handler.session.rollback()  # Make sure this is awaited if it's an async function
            logger.error(f"Failed to change role of member: {e}")
            raise TeamError("Failed to change the role of the member")

