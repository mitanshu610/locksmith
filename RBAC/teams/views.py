from uuid import UUID

from clerk_integration.utils import UserData
from fastapi import Depends

from RBAC.teams.exceptions import TeamError
from RBAC.teams.schemas import TeamCreateSchema, TeamUpdateSchema, TeamMemberAddSchema, TeamGetSchema, \
    OrgMembersQueryParams, TeamMembershipResponse, TeamAddSchema, MemberRoleChangeSchema
from RBAC.teams.services import TeamService, TeamMembershipService
from utils.common import handle_exceptions, get_user_data_from_request
from utils.connection_handler import ConnectionHandler, get_connection_handler_for_app
from utils.serializers import ResponseData


# ---------- Teams ----------
@handle_exceptions("Failed to create team", [TeamError])
async def create_team(
    team_details: TeamAddSchema,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    if not team_details.created_by:
        team_details.created_by = user_data.userId
    service = TeamService(connection_handler)
    new_team = await service.create_team(team_details, user_data.userId, user_data.orgId)
    return ResponseData.model_construct(success=True, data=new_team)


@handle_exceptions("Failed to fetch teams", [TeamError])
async def get_teams_by_user_org(
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    teams = await service.get_teams_by_user_org(user_data.orgId, user_data.userId)
    return ResponseData.model_construct(success=True, data=teams)


@handle_exceptions("Failed to fetch teams", [TeamError])
async def get_team_by_id(
    team_id: UUID,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    team = await service.get_team_by_id(team_id, user_data)
    return ResponseData.model_construct(success=True, data=team)


@handle_exceptions("Failed to update team", [TeamError])
async def update_team(
    team_id: UUID,
    team_details: TeamUpdateSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    updated_team = await service.update_team(team_id, team_details)
    updated_team = TeamCreateSchema.model_validate(updated_team)
    return ResponseData.model_construct(success=True, data=updated_team)


@handle_exceptions("Failed to delete team", [TeamError])
async def delete_team(
    team_id: UUID,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamService(connection_handler)
    await service.delete_team(team_id)
    return ResponseData.model_construct(success=True, message="Team deleted successfully")



# ---------- Team Members ----------
@handle_exceptions("Failed to add team member", [TeamError])
async def add_team_member(
        team_id: UUID,
        members: TeamMemberAddSchema,
        user_data: UserData = Depends(get_user_data_from_request),
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    new_member = await service.add_member(team_id, members, user_data.userId)
    if isinstance(new_member, list):
        response_data = [TeamMembershipResponse.model_validate(member) for member in new_member]
    else:
        response_data = TeamMembershipResponse.model_validate(new_member)

    return ResponseData.model_construct(success=True, data=response_data)


@handle_exceptions("Failed to list team members", [TeamError])
async def get_team_members(
    team_id: UUID,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    members = await service.get_members(team_id)
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


@handle_exceptions("Failed to remove team member", [TeamError])
async def change_role_of_member(
    team_id: UUID,
    member_info: MemberRoleChangeSchema,
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamMembershipService(connection_handler)
    data = await service.change_members_role(member_info, user_data, team_id)
    return ResponseData.model_construct(success=True, message="Role changed successfully", data=data)