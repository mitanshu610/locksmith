from fastapi import APIRouter, Depends
from utils.common import get_user_data_from_request
from RBAC.roles.views import (
    create_team_role, get_all_team_roles
)

router = APIRouter(prefix="/roles", tags=["Roles"], dependencies=[Depends(get_user_data_from_request)])

# --- Team Roles ---
router.add_api_route("/", endpoint=create_team_role, methods=["POST"], description="Create a role (manager/member)")
router.add_api_route("/", endpoint=get_all_team_roles, methods=["GET"], description="Get all roles available for team")
