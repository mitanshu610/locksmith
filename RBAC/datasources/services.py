from collections import defaultdict

from clerk_integration.helpers import ClerkHelper
from clerk_integration.utils import UserData
from sqlalchemy.exc import SQLAlchemyError
from RBAC.datasources.dao import DataSourceAccessDAO
from RBAC.datasources.exceptions import DataSourceAccessError
from RBAC.datasources.schemas import DataSourceAccessSchema
from RBAC.datasources.models import DataSourceAccess
from RBAC.teams.dao import TeamMembershipsDAO, TeamsDAO
from RBAC.teams.exceptions import TeamError
from config.logging import logger
from config.settings import loaded_config
from utils.connection_handler import ConnectionHandler


class DataSourceAccessService:
    def __init__(self, connection_handler: ConnectionHandler):
        self.session = connection_handler.session
        self.dao = DataSourceAccessDAO(self.session)
        self.team_membership_dao = TeamMembershipsDAO(self.session)
        self.clerk_client = ClerkHelper(loaded_config.clerk_secret_key)
        self.teams_dao = TeamsDAO(self.session)

    async def create_access(self, data: DataSourceAccessSchema) -> DataSourceAccess:
        try:
            return await self.dao.create_access(data)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("DB error creating datasource access: %s", str(e))
            raise DataSourceAccessError("Failed to create datasource access")

    async def delete_access(self, datasource_id):
        try:
            await self.dao.delete_access(datasource_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("DB error deleting datasource access: %s", str(e))
            raise TeamError("Failed to delete datasource access")

    async def get_access_by_user(self, user_id):
        results = await self.dao.get_by_user(user_id)
        return [DataSourceAccessSchema.model_validate(result) for result in results]

    async def get_access_by_team(self, team_id):
        results = await self.dao.get_by_team(team_id)
        return [DataSourceAccessSchema.model_validate(result) for result in results]

    async def get_access_by_org(self, org_id):
        results = await self.dao.get_by_org(org_id)
        return [DataSourceAccessSchema.model_validate(result) for result in results]

    async def get_access_by_datasource(self, datasource_id):
        return await self.dao.get_by_datasource(datasource_id)

    async def check_access(self, datasource_id, user_id, team_id, org_id) -> bool:
        return await self.dao.check_access(datasource_id, user_id, team_id, org_id)

    async def get_accessible_datasources_by_user(self, user_id, org_id=None):
        """
        Get all datasources accessible by a user, categorized by access level:
        - Personal: Directly assigned to the user
        - Team: Assigned to any team the user is a member of
        - Organization: Assigned to the user's organization

        Args:
            user_id (str): The ID of the user
            org_id (str, optional): The organization ID of the user. If provided,
                                   also returns datasources accessible by the org.

        Returns:
            dict: A dictionary with categorized datasource access:
                {
                    "personal": [datasource_ids],
                    "team": [datasource_ids],
                    "organization": [datasource_ids]
                }
        """
        try:
            result = {
                "personal": [],
                "team": [],
                "organization": []
            }

            # Get datasources directly accessible by the user
            user_datasources = await self.dao.get_by_user(user_id)
            result["personal"] = [access.datasource_id for access in user_datasources]

            user_teams = await self.team_membership_dao.get_teams_by_user(user_id)

            # Get datasources accessible by user's teams
            team_ids = [team.team_id for team in user_teams]
            for team_id in team_ids:
                team_access = await self.dao.get_by_team(team_id)
                team_datasource_ids = [access.datasource_id for access in team_access]
                result["team"].extend(team_datasource_ids)

            # Remove duplicates in team datasources
            result["team"] = list(set(result["team"]))

            # Get datasources accessible by user's organization (if org_id provided)
            if org_id:
                org_datasources = await self.dao.get_by_org(org_id)
                result["organization"] = [access.datasource_id for access in org_datasources]

            return result

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("DB error retrieving accessible datasources: %s", str(e))
            raise DataSourceAccessError("Failed to retrieve accessible datasources")

    async def get_user_access_status_for_datasource(self, datasource_id: int, user_data: UserData):
        try:
            if not user_data.orgId:
                return []

            org_members_response = await self.clerk_client.get_org_members(user_data.orgId, limit=100)
            org_members = org_members_response.get("members", [])

            access_info = await self.dao.get_users_with_access_status(datasource_id, user_data.orgId)
            all_org_teams = await self.teams_dao.get_teams_by_org(user_data.orgId, user_data.userId)

            team_ids_with_access = access_info["team_access"]

            orgs_with_access = access_info["org_access"]
            org_has_access = user_data.orgId in orgs_with_access

            direct_user_access = access_info["direct_user_access"]

            user_team_membership = defaultdict(list)

            for team in all_org_teams:
                team_id = team["team_id"]
                team_members = await self.team_membership_dao.get_members(team_id, from_clerk=False)

                for member in team_members:
                    user_team_membership[member["user_id"]].append(str(team_id))

            users_result = []
            for user in org_members:
                user_id = user["id"]

                user_teams = user_team_membership.get(user_id, [])

                has_direct_access = user_id in direct_user_access

                has_team_access = any(team_id in team_ids_with_access for team_id in user_teams)

                user_access_data = {
                    "user_id": user_id,
                    "firstName": user.get("firstName"),
                    "lastName": user.get("lastName"),
                    "role": user.get("role"),
                    "has_access": has_direct_access,
                    "team_access": has_team_access,
                    "org_access": org_has_access
                }

                users_result.append(user_access_data)

            teams_result = []
            for team in all_org_teams:
                team_id = team["team_id"]
                team_data = {
                    "team_id": str(team_id),
                    "team_name": team["name"],
                    "has_access": team_id in team_ids_with_access
                }
                teams_result.append(team_data)

            org_result = {
                "org_id": user_data.orgId,
                "has_access": org_has_access
            }

            result = {
                "users": users_result,
                "teams": teams_result,
                "org": org_result
            }

            return result
        except Exception as e:
            logger.error(f"Error getting user access status: {e}")
            return []

    async def revoke_specific_access(self, datasource_id, user_id=None, team_id=None, org_id=None):
        """
        Revoke access for a specific user, team, or organization to a datasource.

        Args:
            datasource_id: The ID of the datasource
            user_id: Optional user ID to revoke access for
            team_id: Optional team ID to revoke access for
            org_id: Optional organization ID to revoke access for

        Returns:
            bool: True if access was revoked, False if no matching access record was found

        Raises:
            DataSourceAccessError: If there was an error during the database operation
        """
        provided_ids = [user_id, team_id, org_id]
        if sum(selected_id is not None for selected_id in provided_ids) != 1:
            raise DataSourceAccessError("Exactly one of user_id, team_id, or org_id must be provided")

        try:
            await self.dao.delete_specific_access(datasource_id, user_id, team_id, org_id)
        except (SQLAlchemyError, Exception) as e:
            await self.session.rollback()
            logger.error(f"DB error revoking specific datasource access: {str(e)}")
            raise DataSourceAccessError("Failed to revoke specific datasource access")

    async def get_all_entities_with_access_details(self, datasource_id: int):
        try:
            # Get all entity IDs with access
            entities = await self.dao.get_all_entities_with_access(datasource_id)

            # Get detailed information for each entity

            # 1. Users
            users_details = []
            for user_id in entities["user_ids"]:
                try:
                    users_details.append(user_id)
                except Exception as e:
                    logger.warning(f"Error fetching user details for {user_id}: {e}")
                    users_details.append(user_id)

            # 2. Teams
            teams_details = []
            for team_id in entities["team_ids"]:
                try:
                    teams_details.append(str(team_id))
                except Exception as e:
                    logger.warning(f"Error fetching team details for {team_id}: {e}")
                    teams_details.append(str(team_id))

            # 3. Organizations
            orgs_details = []
            for org_id in entities["org_ids"]:
                try:
                    orgs_details.append(org_id)
                except Exception as e:
                    logger.warning(f"Error fetching org details for {org_id}: {e}")
                    orgs_details.append(org_id)

            return {
                "datasource_id": datasource_id,
                "users": users_details,
                "teams": teams_details,
                "organizations": orgs_details
            }

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"DB error retrieving datasource access details: {str(e)}")
            raise DataSourceAccessError("Failed to retrieve datasource access details")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error retrieving datasource access details: {str(e)}")
            raise DataSourceAccessError(f"Failed to retrieve datasource access details: {str(e)}")
