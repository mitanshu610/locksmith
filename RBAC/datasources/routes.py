from fastapi import APIRouter
from RBAC.datasources.views import (
    check_access, create_access, delete_access, get_all_accessible_sources, get_datasource_share_details,
    get_team_access, get_org_access, revoke_datasource_access, get_full_datasource_access_details
)

router = APIRouter(prefix="/datasources", tags=["DataSources"])

router.add_api_route("/access", endpoint=create_access, methods=["POST"], description="Assign access to a datasource (user/team/org)")
router.add_api_route("/access", endpoint=delete_access, methods=["DELETE"], description="Revoke access to a datasource")
router.add_api_route("/check/access", endpoint=check_access, methods=["POST"], description="Check the datasource access")
router.add_api_route("/access/datasource/{datasource_id}", endpoint=get_full_datasource_access_details, methods=["GET"], description="Get all accesses for a datasource")
router.add_api_route("/access", endpoint=get_all_accessible_sources, methods=["GET"], description="Get all accessible datasources")
router.add_api_route("/specific/access", endpoint=revoke_datasource_access, methods=["POST"], description="Revoke specific accesses")
router.add_api_route("/has-and-hasnot/access/{datasource_id}", get_datasource_share_details, methods=["GET"], description="Get all accessible datasources")
router.add_api_route("/access/team/{team_id}", endpoint=get_team_access, methods=["GET"], description="List all datasources a team can access")
router.add_api_route("/access/org/{org_id}", endpoint=get_org_access, methods=["GET"], description="List all datasources an org can access")