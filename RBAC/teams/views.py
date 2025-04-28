from uuid import UUID

from clerk_integration.utils import UserData
from fastapi import Depends

from RBAC.teams.exceptions import TeamError
from RBAC.teams.schemas import TeamCreateSchema, TeamUpdateSchema, TeamMemberAddSchema, TeamGetSchema, \
    OrgMembersQueryParams
from RBAC.teams.services import TeamService, TeamMembershipService
from utils.common import handle_exceptions, get_user_data_from_request
from utils.connection_handler import ConnectionHandler, get_connection_handler_for_app
from utils.serializers import ResponseData


# ---------- Teams ----------
@handle_exceptions("Failed to create team", [TeamError])
async def create_team(
    team_details: TeamCreateSchema,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    if not team_details.created_by:
        team_details.created_by = user_data.userId
    service = TeamService(connection_handler)
    new_team = await service.create_team(team_details, user_data.userId, user_data.orgId)
    return ResponseData.model_construct(success=True, data=new_team)


@handle_exceptions("Failed to fetch teams", [TeamError])
async def get_teams_by_org(
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    teams = await service.get_teams_by_org(user_data.orgId)
    return ResponseData.model_construct(success=True, data=[TeamGetSchema.model_validate(t) for t in teams])


@handle_exceptions("Failed to fetch teams", [TeamError])
async def get_team_by_id(
    team_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    team = await service.get_team_by_id(team_id)
    return ResponseData.model_construct(success=True, data=TeamCreateSchema.model_validate(team))


@handle_exceptions("Failed to update team", [TeamError])
async def update_team(
    team_id: str,
    team_details: TeamUpdateSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    updated_team = await service.update_team(team_id, team_details)
    updated_team = TeamCreateSchema.model_validate(updated_team)
    return ResponseData.model_construct(success=True, data=updated_team)


@handle_exceptions("Failed to delete team", [TeamError])
async def delete_team(
    team_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    await service.delete_team(team_id)
    return ResponseData.model_construct(success=True, message="Team deleted successfully")



# ---------- Team Members ----------
@handle_exceptions("Failed to add team member", [TeamError])
async def add_team_member(
    team_id: UUID,
    member: TeamMemberAddSchema,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    new_member = await service.add_member(team_id, member, user_data.userId)
    new_member = TeamMemberAddSchema.model_validate(new_member)
    return ResponseData.model_construct(success=True, data=new_member)


@handle_exceptions("Failed to list team members", [TeamError])
async def get_team_members(
    team_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    members = await service.get_members(team_id)
    print(members)
    return ResponseData.model_construct(success=True, data=members)


@handle_exceptions("Failed to remove team member", [TeamError])
async def remove_team_member(
    team_id: UUID,
    user_id: str,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    await service.remove_member(team_id, user_id, user_data.userId)
    return ResponseData.model_construct(success=True, message="Member removed successfully")

@handle_exceptions("Failed to remove team member", [TeamError])
async def get_org_members(
    query_params: OrgMembersQueryParams = Depends(),
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    org_members = await service.get_org_members(query_params, user_data)
    return ResponseData.model_construct(success=True, data=org_members)