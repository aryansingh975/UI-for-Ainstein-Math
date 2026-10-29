from fastapi import APIRouter
from .problems import router as problems_router
from .sessions import router as sessions_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(problems_router, tags=["Problems"])
api_v1_router.include_router(sessions_router, tags=["Sessions"])

