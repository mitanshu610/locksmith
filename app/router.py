from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse

from config.settings import loaded_config

from RBAC.teams.routes import router as teams_router
from RBAC.roles.routes import router as roles_router


async def healthz():
    return JSONResponse(status_code=200, content={"success": True})


api_router = APIRouter()

""" all version v1.0 routes """
api_router_v1 = APIRouter(prefix='/v1.0')

# all routes to public server
if loaded_config.server_type == "public":
    api_router_v1.include_router(teams_router)
    api_router_v1.include_router(roles_router)
else:
    """ all common routes """

""" health check routes """
api_router_healthz = APIRouter()
api_router_healthz.add_api_route("/_healthz", methods=['GET'], endpoint=healthz, include_in_schema=False)
api_router_healthz.add_api_route("/_readyz", methods=['GET'], endpoint=healthz, include_in_schema=False)

api_router.include_router(api_router_healthz)
api_router.include_router(api_router_v1)



