from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.requirements import router as requirements_router
from app.api.v1.issues import router as issues_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.events import router as events_router
from app.api.v1.traceability import router as traceability_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.search import router as search_router
from app.api.v1.reports import router as reports_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.settings import router as settings_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, prefix="", tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# NOTE: reports must be registered BEFORE /projects/{project_id} so the
# literal '/report' paths win over the path parameter route.
api_v1_router.include_router(reports_router, prefix="/projects", tags=["Reports"])
api_v1_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_v1_router.include_router(requirements_router, prefix="/requirements", tags=["Requirements"])
api_v1_router.include_router(issues_router, prefix="/issues", tags=["Issues"])
api_v1_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_v1_router.include_router(events_router, prefix="/events", tags=["Events"])
api_v1_router.include_router(traceability_router, prefix="/traceability", tags=["Traceability"])
api_v1_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_v1_router.include_router(search_router, prefix="/search", tags=["Search"])
api_v1_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_v1_router.include_router(settings_router, prefix="/org", tags=["Settings & Rules"])
