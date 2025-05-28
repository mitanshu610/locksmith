from typing import Optional
from uuid import UUID

from clerk_integration.utils import UserData
from fastapi import Depends

from RBAC.datasources.exceptions import DataSourceAccessError
from utils.connection_handler import ConnectionHandler, get_connection_handler_for_app
from utils.serializers import ResponseData
from utils.common import handle_exceptions, get_user_data_from_request
from RBAC.datasources.schemas import DataSourceAccessSchema, RevokeAccessSchema
from RBAC.datasources.services import DataSourceAccessService


@handle_exceptions("Failed to create access", [DataSourceAccessError])
async def create_access(
    data: DataSourceAccessSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    await service.create_access(data)
    return ResponseData.model_construct(success=True, message="Successfully created access!")


@handle_exceptions("Failed to delete access", [DataSourceAccessError])
async def delete_access(
    datasource_id: int,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    await service.delete_access(datasource_id)
    return ResponseData.model_construct(success=True, message="Successfully revoked access!")




@handle_exceptions("Failed to get user access", [DataSourceAccessError])
async def get_user_access(
    user_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_access_by_user(user_id)
    return ResponseData.model_construct(success=True, data=data)


@handle_exceptions("Failed to get team access", [DataSourceAccessError])
async def get_team_access(
    team_id: UUID,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_access_by_team(team_id)
    return ResponseData.model_construct(success=True, data=data)


@handle_exceptions("Failed to get org access", [DataSourceAccessError])
async def get_org_access(
    org_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_access_by_org(org_id)
    return ResponseData.model_construct(success=True, data=data)


@handle_exceptions("Failed to get datasource access", [DataSourceAccessError])
async def get_datasource_access(
    datasource_id: int,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_access_by_datasource(datasource_id)
    data = DataSourceAccessSchema.model_validate(data)
    return ResponseData.model_construct(success=True, data=data)


@handle_exceptions("Failed to check access", [DataSourceAccessError])
async def check_access(
    data: DataSourceAccessSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    has_access = await service.check_access(
        data.datasource_id,
        data.user_id,
        data.team_id,
        data.org_id,
    )
    return ResponseData.model_construct(success=True, data={"access": has_access})


@handle_exceptions("Failed to check access", [DataSourceAccessError])
async def get_all_accessible_sources(
    user_id: str,
    org_id: Optional[str] = None,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_accessible_datasources_by_user(user_id, org_id)
    return ResponseData.model_construct(success=True, data=data)


@handle_exceptions("Failed to get datasource share details", [DataSourceAccessError])
async def get_datasource_share_details(
        datasource_id: int,
        user_data: UserData = Depends(get_user_data_from_request),
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    data = await service.get_user_access_status_for_datasource(datasource_id, user_data)
    return ResponseData.model_construct(
        success=True,
        data=data,
        message="Successfully retrieved datasource share details"
    )

@handle_exceptions("Failed to get datasource share details", [DataSourceAccessError])
async def revoke_datasource_access(
    data: RevokeAccessSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    await service.revoke_specific_access(
        data.datasource_id,
        data.user_id,
        data.team_id,
        data.org_id
    )
    return ResponseData.model_construct(
        success=True,
        message="Successfully revoked datasource access"
    )


@handle_exceptions("Failed to get datasource access details", [DataSourceAccessError])
async def get_full_datasource_access_details(
        datasource_id: int,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    service = DataSourceAccessService(connection_handler)
    access_data = await service.get_all_entities_with_access_details(datasource_id)

    return ResponseData.model_construct(
        success=True,
        data=access_data,
        message="Successfully retrieved datasource access details"
    )
