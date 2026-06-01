from fastapi import APIRouter
from app.api.endpoints import admin, auth, interview_types, interviews, progress, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(interview_types.router, prefix="/interview-types", tags=["interview-types"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
