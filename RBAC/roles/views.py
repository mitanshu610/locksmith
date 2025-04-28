from fastapi import Depends
from utils.connection_handler import ConnectionHandler, get_connection_handler_for_app
from utils.serializers import ResponseData
from utils.common import handle_exceptions
from RBAC.teams.exceptions import TeamError
from RBAC.roles.schemas import TeamRoleSchema

from RBAC.roles.services import TeamRoleService


@handle_exceptions("Failed to create team role", [TeamError])
async def create_team_role(
    role: TeamRoleSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamRoleService(connection_handler)
    new_role = await service.create_role(role)
    new_role = TeamRoleSchema.model_validate(new_role)
    return ResponseData.model_construct(success=True, data=new_role)


@handle_exceptions("Failed to fetch team roles", [TeamError])
async def get_all_team_roles(
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = TeamRoleService(connection_handler)
    roles = await service.get_all_roles()
    return ResponseData(success=True, data=roles)
