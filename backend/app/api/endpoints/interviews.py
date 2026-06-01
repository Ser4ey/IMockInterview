from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.interview import InterviewResult, InterviewSession, Message
from app.models.user import User
from app.schemas.interview import (
    InterviewResultRead,
    InterviewSessionCreate,
    InterviewSessionRead,
    InterviewTurnRead,
    MessageCreate,
    MessageRead,
)
from app.services.interview_engine import interview_engine
from app.services.limits import LimitExceededError, limit_service
from app.services.serialization import loads_list

router = APIRouter()


async def get_owned_session(
    db: AsyncSession,
    session_id: int,
    current_user: User,
) -> InterviewSession:
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .options(
            selectinload(InterviewSession.interview_type),
            selectinload(InterviewSession.current_question),
        )
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Интервью не найдено")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return session


@router.post("", response_model=InterviewSessionRead)
async def create_interview(
    interview_in: InterviewSessionCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    try:
        session = await interview_engine.create_session(db, current_user.id, interview_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _serialize_session(session)


@router.get("", response_model=list[InterviewSessionRead])
async def list_interviews(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .options(selectinload(InterviewSession.interview_type), selectinload(InterviewSession.current_question))
        .order_by(InterviewSession.started_at.desc(), InterviewSession.id.desc())
    )
    return [_serialize_session(session) for session in result.scalars().all()]


@router.get("/history", response_model=list[InterviewSessionRead])
async def read_history(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return await list_interviews(db=db, current_user=current_user)


@router.post("/{session_id}/messages", response_model=InterviewTurnRead)
async def create_message(
    session_id: int,
    message_in: MessageCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    session = await get_owned_session(db, session_id, current_user)
    try:
        await limit_service.consume_interview_message(db, current_user)
        updated_session, messages, result = await interview_engine.submit_user_answer(
            db,
            session,
            message_in.content,
        )
    except LimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "session": _serialize_session(updated_session),
        "messages": messages,
        "result": _serialize_result(result) if result else None,
    }


@router.post("/{session_id}/finish", response_model=InterviewTurnRead)
async def finish_interview(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    session = await get_owned_session(db, session_id, current_user)
    updated_session, result = await interview_engine.finish_session(db, session)
    return {"session": _serialize_session(updated_session), "messages": [], "result": _serialize_result(result)}


@router.get("/{session_id}", response_model=InterviewSessionRead)
async def read_interview(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return _serialize_session(await get_owned_session(db, session_id, current_user))


@router.get("/{session_id}/messages", response_model=list[MessageRead])
async def read_messages(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    await get_owned_session(db, session_id, current_user)
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    return result.scalars().all()


@router.get("/{session_id}/result", response_model=InterviewResultRead)
async def read_result(
    session_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    await get_owned_session(db, session_id, current_user)
    result = await db.execute(select(InterviewResult).where(InterviewResult.session_id == session_id))
    interview_result = result.scalars().first()
    if not interview_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Результат интервью не найден")
    return _serialize_result(interview_result)


def _serialize_session(session: InterviewSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "interview_type_id": session.interview_type_id,
        "interview_type_title": session.interview_type.title,
        "role": session.interview_type.role,
        "technology_stack": session.interview_type.technology_stack,
        "level": session.level,
        "status": session.status,
        "stage": session.stage,
        "current_question_id": session.current_question_id,
        "question_index": session.question_index,
        "started_at": session.started_at,
        "finished_at": session.finished_at,
    }


def _serialize_result(result: InterviewResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "session_id": result.session_id,
        "score": result.score,
        "correctness": result.correctness,
        "completeness": result.completeness,
        "depth": result.depth,
        "communication": result.communication,
        "strengths": loads_list(result.strengths),
        "weaknesses": loads_list(result.weaknesses),
        "recommendations": result.recommendations,
        "summary": result.summary,
        "created_at": result.created_at,
    }
