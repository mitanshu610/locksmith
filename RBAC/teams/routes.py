from fastapi import APIRouter, Depends
from utils.common import get_user_data_from_request
from RBAC.teams.views import (
    create_team,
    update_team,
    delete_team,
    get_teams_by_user_org,
    add_team_member,
    remove_team_member,
    get_team_members,
    get_team_by_id, get_org_members, change_role_of_member
)

router = APIRouter(prefix="/teams", tags=["Teams"])

# --- Teams ---
router.add_api_route("/", endpoint=create_team, methods=["POST"], description="Create a new team in an org")
router.add_api_route("/", endpoint=get_teams_by_user_org, methods=["GET"], description="Get all teams in the org")
router.add_api_route("/{team_id}", endpoint=get_team_by_id, methods=["GET"], description="Get a team by ID")
router.add_api_route("/{team_id}", endpoint=update_team, methods=["PUT"], description="Update team name or slug", dependencies=[Depends(get_user_data_from_request)])
router.add_api_route("/{team_id}", endpoint=delete_team, methods=["DELETE"], description="Delete a team", dependencies=[Depends(get_user_data_from_request)])

# --- Memberships ---
router.add_api_route("/{team_id}/members", endpoint=add_team_member, methods=["POST"], description="Add member to team")
router.add_api_route("/{team_id}/members", endpoint=get_team_members, methods=["GET"], description="List team members", dependencies=[Depends(get_user_data_from_request)])
router.add_api_route("/{team_id}/members/{user_id}", endpoint=remove_team_member, methods=["DELETE"], description="Remove member from team")
router.add_api_route("/{team_id}/members", endpoint=change_role_of_member, methods=["PATCH"], description="Change member role")


org_router = APIRouter(prefix="/org", tags=["Organizations"])
org_router.add_api_route("/members", endpoint=get_org_members, methods=["GET"], description="Get all members of an org")