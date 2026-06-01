import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.interview import InterviewType, Question, QuestionGenerationJob
from app.models.user import User
from app.schemas.interview import (
    InterviewTypeCreate,
    InterviewTypeRead,
    InterviewTypeUpdate,
    QuestionCreate,
    QuestionGenerationJobRead,
    QuestionGenerationRequest,
    QuestionRead,
    QuestionUpdate,
)
from app.services.question_generation import question_generation_service
from app.services.question_quality import build_question_hash
from app.services.serialization import dumps_list, loads_list

router = APIRouter()


@router.get("/health")
async def health() -> Any:
    return {"status": "ok", "service": "IMock API"}


@router.get("/interview-types", response_model=list[InterviewTypeRead])
async def list_interview_types(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    result = await db.execute(select(InterviewType).order_by(InterviewType.created_at.desc(), InterviewType.id.desc()))
    items = result.scalars().all()
    return [await _serialize_interview_type(db, item) for item in items]


@router.post("/interview-types", response_model=InterviewTypeRead)
async def create_interview_type(
    payload: InterviewTypeCreate,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    existing = await db.scalar(select(InterviewType).where(InterviewType.title == payload.title))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тип собеседования уже существует")
    item = InterviewType(
        title=payload.title,
        role=payload.role,
        technology_stack=payload.technology_stack,
        description=payload.description,
        levels=dumps_list(payload.levels),
        is_active=payload.is_active,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    if payload.auto_generate_questions:
        for level in payload.levels:
            await question_generation_service.generate_questions(db, item, level, payload.questions_per_level)
        await db.refresh(item)
    return await _serialize_interview_type(db, item)


@router.patch("/interview-types/{interview_type_id}", response_model=InterviewTypeRead)
async def update_interview_type(
    interview_type_id: int,
    payload: InterviewTypeUpdate,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    item = await db.get(InterviewType, interview_type_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип собеседования не найден")
    data = payload.model_dump(exclude_unset=True)
    if "levels" in data:
        item.levels = dumps_list(data.pop("levels"))
    for key, value in data.items():
        setattr(item, key, value)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await _serialize_interview_type(db, item)


@router.post("/interview-types/{interview_type_id}/generate-questions", response_model=QuestionGenerationJobRead)
async def generate_questions(
    interview_type_id: int,
    payload: QuestionGenerationRequest,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    interview_type = await db.get(InterviewType, interview_type_id)
    if not interview_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип собеседования не найден")
    if payload.level not in loads_list(interview_type.levels):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Уровень не доступен для этого типа")
    job = await question_generation_service.generate_questions(
        db,
        interview_type,
        payload.level,
        payload.requested_count,
    )
    return _serialize_generation_job(job, interview_type.title)


@router.get("/questions", response_model=list[QuestionRead])
async def list_questions(
    interview_type_id: int | None = None,
    level: str | None = None,
    tag: str | None = Query(default=None),
    include_disabled: bool = False,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    stmt = select(Question).options(selectinload(Question.interview_type), selectinload(Question.source))
    if interview_type_id is not None:
        stmt = stmt.where(Question.interview_type_id == interview_type_id)
    if level:
        stmt = stmt.where(Question.level == level.lower())
    if not include_disabled:
        stmt = stmt.where(Question.is_active.is_(True))
    stmt = stmt.order_by(Question.created_at.desc(), Question.id.desc())
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    if tag:
        lowered_tag = tag.lower()
        items = [item for item in items if lowered_tag in [value.lower() for value in loads_list(item.tags)]]
    return [_serialize_question(item) for item in items]


@router.post("/questions", response_model=QuestionRead)
async def create_question(
    payload: QuestionCreate,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    interview_type = await db.get(InterviewType, payload.interview_type_id)
    if not interview_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип собеседования не найден")
    if payload.level not in loads_list(interview_type.levels):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Уровень не доступен для этого типа")
    item = Question(
        interview_type_id=payload.interview_type_id,
        level=payload.level,
        question_text=payload.question_text,
        expected_answer=payload.expected_answer,
        evaluation_criteria=dumps_list(payload.evaluation_criteria),
        tags=dumps_list(payload.tags),
        question_hash=build_question_hash(payload.interview_type_id, payload.level, payload.question_text),
        source_id=payload.source_id,
        is_active=payload.is_active,
    )
    db.add(item)
    await db.commit()
    result = await db.execute(
        select(Question)
        .where(Question.id == item.id)
        .options(selectinload(Question.interview_type), selectinload(Question.source))
    )
    return _serialize_question(result.scalars().one())


@router.patch("/questions/{question_id}", response_model=QuestionRead)
async def update_question(
    question_id: int,
    payload: QuestionUpdate,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.interview_type), selectinload(Question.source))
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден")
    data = payload.model_dump(exclude_unset=True)
    if "evaluation_criteria" in data:
        item.evaluation_criteria = dumps_list(data.pop("evaluation_criteria") or [])
    if "tags" in data:
        item.tags = dumps_list(data.pop("tags") or [])
    for key, value in data.items():
        setattr(item, key, value)
    item.question_hash = build_question_hash(item.interview_type_id, item.level, item.question_text)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _serialize_question(item)


@router.patch("/questions/{question_id}/disable", response_model=QuestionRead)
async def disable_question(
    question_id: int,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    return await _set_question_activity(db, question_id, False)


@router.patch("/questions/{question_id}/enable", response_model=QuestionRead)
async def enable_question(
    question_id: int,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    return await _set_question_activity(db, question_id, True)


@router.get("/question-generation-jobs", response_model=list[QuestionGenerationJobRead])
async def list_generation_jobs(
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    result = await db.execute(
        select(QuestionGenerationJob)
        .options(selectinload(QuestionGenerationJob.interview_type))
        .order_by(QuestionGenerationJob.created_at.desc(), QuestionGenerationJob.id.desc())
    )
    return [
        _serialize_generation_job(job, job.interview_type.title if job.interview_type else None)
        for job in result.scalars().all()
    ]


async def _set_question_activity(db: AsyncSession, question_id: int, is_active: bool) -> QuestionRead:
    result = await db.execute(
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.interview_type), selectinload(Question.source))
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вопрос не найден")
    item.is_active = is_active
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _serialize_question(item)


async def _serialize_interview_type(db: AsyncSession, item: InterviewType) -> dict[str, Any]:
    counts_result = await db.execute(
        select(Question.level, func.count(Question.id))
        .where(Question.interview_type_id == item.id, Question.is_active.is_(True))
        .group_by(Question.level)
    )
    counts = {level: count for level, count in counts_result.all()}
    return {
        "id": item.id,
        "title": item.title,
        "role": item.role,
        "technology_stack": item.technology_stack,
        "description": item.description,
        "levels": loads_list(item.levels),
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "question_counts": counts,
    }


def _serialize_question(item: Question) -> dict[str, Any]:
    return {
        "id": item.id,
        "interview_type_id": item.interview_type_id,
        "interview_type_title": item.interview_type.title if item.interview_type else None,
        "level": item.level,
        "question_text": item.question_text,
        "expected_answer": item.expected_answer,
        "evaluation_criteria": loads_list(item.evaluation_criteria),
        "tags": loads_list(item.tags),
        "question_hash": item.question_hash,
        "source_id": item.source_id,
        "source": item.source,
        "is_active": item.is_active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _serialize_generation_job(job: QuestionGenerationJob, title: str | None) -> dict[str, Any]:
    return {
        "id": job.id,
        "interview_type_id": job.interview_type_id,
        "interview_type_title": title,
        "level": job.level,
        "status": job.status,
        "requested_count": job.requested_count,
        "generated_count": job.generated_count,
        "skipped_count": job.skipped_count,
        "provider": job.provider,
        "context_used": job.context_used,
        "raw_response_preview": job.raw_response_preview,
        "input_tokens": job.input_tokens,
        "output_tokens": job.output_tokens,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }
