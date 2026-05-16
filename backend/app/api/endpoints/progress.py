from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.interview import InterviewResult, InterviewSession, InterviewStatus
from app.models.user import User
from app.schemas.interview import ProgressRead
from app.services.limits import limit_service

router = APIRouter()


@router.get("", response_model=ProgressRead)
async def read_progress(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    total = await db.scalar(
        select(func.count(InterviewSession.id)).where(InterviewSession.user_id == current_user.id)
    )
    completed = await db.scalar(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == InterviewStatus.FINISHED.value,
        )
    )
    average_score = await db.scalar(
        select(func.avg(InterviewResult.score))
        .join(InterviewSession, InterviewResult.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == current_user.id)
    )
    limit_status = await limit_service.get_status(db, current_user)
    await db.commit()
    return ProgressRead(
        total_interviews=total or 0,
        completed_interviews=completed or 0,
        average_score=round(float(average_score or 0), 2),
        weak_criteria=[],
        daily_limit=limit_status.daily_limit,
        used_today=limit_status.used_today,
        remaining_today=limit_status.remaining_today,
        reset_at=limit_status.reset_at,
    )
