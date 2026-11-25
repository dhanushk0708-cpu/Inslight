from fastapi import APIRouter
from app.api.v1.routes import (
    auth,
    health,
    datasets,
    query,
    profile,
    deep_dive,
    what_if,
    anomalies,
    reports,
    gmail,
    bi_agent,
    root_cause,
    forecasting,
    advanced_anomalies,
    alerts,
    data_quality,
    comparisons,
    dashboards,
    relationships,
    notifications,
    admin,
    presentations,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(datasets.router)
api_router.include_router(query.router)
api_router.include_router(profile.router)
api_router.include_router(deep_dive.router)
api_router.include_router(what_if.router)
api_router.include_router(anomalies.router)
api_router.include_router(reports.router)
api_router.include_router(gmail.router)
api_router.include_router(bi_agent.router)
api_router.include_router(root_cause.router)
api_router.include_router(forecasting.router)
api_router.include_router(advanced_anomalies.router)
api_router.include_router(alerts.router)
api_router.include_router(data_quality.router)
api_router.include_router(comparisons.router)
api_router.include_router(dashboards.router)
api_router.include_router(relationships.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
api_router.include_router(presentations.router)
