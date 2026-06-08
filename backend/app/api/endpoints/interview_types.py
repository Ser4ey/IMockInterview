from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.interview import InterviewType, Question
from app.models.user import User
from app.schemas.interview import InterviewTypeRead
from app.services.serialization import loads_list

router = APIRouter()


@router.get("", response_model=list[InterviewTypeRead])
async def list_interview_types(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_active_user),
) -> Any:
    result = await db.execute(
        select(InterviewType)
        .where(InterviewType.is_active.is_(True))
        .order_by(InterviewType.title.asc())
    )
    items = result.scalars().all()
    return [await _serialize_interview_type(db, item) for item in items]


async def _serialize_interview_type(db: AsyncSession, item: InterviewType) -> dict[str, Any]:
    counts_result = await db.execute(
        select(Question.level, func.count(Question.id))
        .where(Question.interview_type_id == item.id, Question.is_active.is_(True))
        .group_by(Question.level)
    )
    return {
        "id": item.id,
        "title": item.title,
        "role": item.role,
        "technology_stack": item.technology_stack,
        "description": item.description,
        "levels": loads_list(item.levels),
        "default_question_count": item.default_question_count,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "question_counts": {level: count for level, count in counts_result.all()},
    }
