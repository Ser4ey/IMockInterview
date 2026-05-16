from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.models.user import User
from app.schemas import user as user_schema

router = APIRouter()


@router.get("/me", response_model=user_schema.User)
async def read_current_user(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user
