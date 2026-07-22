"""
Aggregates all v1 endpoint routers under a single APIRouter mounted at
/api/v1 in app.main.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, requests, assignments, categories, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(requests.router)
api_router.include_router(assignments.router)
api_router.include_router(reports.router)
