import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import (
    InterviewResult,
    InterviewSession,
    InterviewStage,
    InterviewStatus,
    InterviewType,
    Message,
    MessageSender,
    Question,
)
from app.schemas.interview import InterviewSessionCreate
from app.services.llm_client import LLMEvaluation, LLMInterviewerReply, llm_client
from app.services.serialization import dumps_list, loads_list

logger = logging.getLogger(__name__)
MAX_INTERVIEW_QUESTION_COUNT = 10


class InterviewEngine:
    async def create_session(
        self,
        db: AsyncSession,
        user_id: int,
        interview_in: InterviewSessionCreate,
    ) -> InterviewSession:
        interview_type = await db.get(InterviewType, interview_in.interview_type_id)
        if not interview_type or not interview_type.is_active:
            raise ValueError("Тип собеседования не найден или отключён")
        if interview_in.level not in loads_list(interview_type.levels):
            raise ValueError("Выбранный уровень недоступен для этого типа собеседования")

        questions = await self._get_active_questions(db, interview_type.id, interview_in.level)
        if not questions:
            raise ValueError("Для выбранного типа и уровня пока нет активных вопросов")

        question_limit = self._resolve_question_limit(
            requested_count=interview_in.question_count,
            default_count=interview_type.default_question_count,
            available_count=len(questions),
        )
        first_question = questions[0]
        session = InterviewSession(
            user_id=user_id,
            interview_type_id=interview_type.id,
            level=interview_in.level,
            stage=InterviewStage.QUESTION.value,
            current_question_id=first_question.id,
            question_index=0,
            question_limit=question_limit,
        )
        db.add(session)
        await db.flush()
        db.add(
            Message(
                session_id=session.id,
                question_id=first_question.id,
                sender=MessageSender.AI.value,
                content=self._format_question(first_question, session.question_index),
            )
        )
        await db.commit()
        return await self._get_session(db, session.id)

    async def submit_user_answer(
        self,
        db: AsyncSession,
        session: InterviewSession,
        content: str,
    ) -> tuple[InterviewSession, list[Message], InterviewResult | None]:
        if session.status == InterviewStatus.FINISHED.value:
            raise ValueError("Собеседование уже завершено")

        session = await self._get_session(db, session.id)
        current_question = session.current_question
        if not current_question:
            raise ValueError("Текущий вопрос не найден")

        user_message = Message(
            session_id=session.id,
            question_id=current_question.id,
            sender=MessageSender.USER.value,
            content=content,
        )
        db.add(user_message)
        await db.flush()

        messages_to_return = [user_message]
        result = None
        history = await self._get_messages(db, session.id)
        interviewer_reply = await self._safe_generate_follow_up(session, current_question, history)
        should_follow_up = session.stage == InterviewStage.QUESTION.value and interviewer_reply.should_ask_follow_up

        if should_follow_up:
            session.stage = InterviewStage.FOLLOW_UP.value
            ai_message = Message(
                session_id=session.id,
                question_id=current_question.id,
                sender=MessageSender.AI.value,
                content=interviewer_reply.message,
            )
            db.add(ai_message)
            messages_to_return.append(ai_message)
        else:
            next_question = await self._get_next_question(db, session)
            if next_question:
                session.question_index += 1
                session.current_question_id = next_question.id
                session.stage = InterviewStage.QUESTION.value
                ai_message = Message(
                    session_id=session.id,
                    question_id=next_question.id,
                    sender=MessageSender.AI.value,
                    content=self._format_question(next_question, session.question_index),
                )
                db.add(ai_message)
                messages_to_return.append(ai_message)
            else:
                result = await self._finish_session(db, session)
                ai_message = Message(
                    session_id=session.id,
                    sender=MessageSender.AI.value,
                    content="Собеседование завершено. Я подготовил итоговую оценку и рекомендации.",
                )
                db.add(ai_message)
                messages_to_return.append(ai_message)

        await db.commit()
        session = await self._get_session(db, session.id)
        refreshed_messages = []
        for message in messages_to_return:
            refreshed = await db.get(Message, message.id)
            if refreshed:
                refreshed_messages.append(refreshed)
        if result:
            await db.refresh(result)
        return session, refreshed_messages, result

    async def finish_session(
        self,
        db: AsyncSession,
        session: InterviewSession,
    ) -> tuple[InterviewSession, InterviewResult]:
        session = await self._get_session(db, session.id)
        if session.status != InterviewStatus.FINISHED.value:
            result = await self._finish_session(db, session)
            db.add(
                Message(
                    session_id=session.id,
                    sender=MessageSender.AI.value,
                    content="Собеседование завершено досрочно. Итог сформирован по уже полученным ответам.",
                )
            )
            await db.commit()
            session = await self._get_session(db, session.id)
            await db.refresh(result)
            return session, result

        result = await self._get_or_create_result(db, session)
        await db.commit()
        return session, result

    async def _finish_session(self, db: AsyncSession, session: InterviewSession) -> InterviewResult:
        session.status = InterviewStatus.FINISHED.value
        session.stage = InterviewStage.FINISHED.value
        session.finished_at = datetime.now(timezone.utc)
        return await self._get_or_create_result(db, session)

    async def _get_or_create_result(self, db: AsyncSession, session: InterviewSession) -> InterviewResult:
        existing = await db.scalar(select(InterviewResult).where(InterviewResult.session_id == session.id))
        if existing:
            return existing

        history = await self._get_messages(db, session.id)
        questions = await self._get_session_questions(db, session.id)
        evaluation = await self._safe_evaluate(session, questions, history)
        interview_result = InterviewResult(
            session_id=session.id,
            score=evaluation.score,
            correctness=evaluation.correctness,
            completeness=evaluation.completeness,
            depth=evaluation.depth,
            communication=evaluation.communication,
            strengths=dumps_list(evaluation.strengths),
            weaknesses=dumps_list(evaluation.weaknesses),
            recommendations=evaluation.recommendations,
            summary=evaluation.summary,
        )
        db.add(interview_result)
        await db.flush()
        return interview_result

    async def _get_session(self, db: AsyncSession, session_id: int) -> InterviewSession:
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
            raise ValueError("Собеседование не найдено")
        return session

    async def _get_messages(self, db: AsyncSession, session_id: int) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(result.scalars().all())

    async def _get_active_questions(self, db: AsyncSession, interview_type_id: int, level: str) -> list[Question]:
        result = await db.execute(
            select(Question)
            .where(
                Question.interview_type_id == interview_type_id,
                Question.level == level,
                Question.is_active.is_(True),
            )
            .order_by(Question.id.asc())
        )
        return list(result.scalars().all())

    async def _get_next_question(self, db: AsyncSession, session: InterviewSession) -> Question | None:
        if session.question_limit and session.question_index + 1 >= session.question_limit:
            return None

        questions = await self._get_active_questions(db, session.interview_type_id, session.level)
        current_ids = [question.id for question in questions]
        if session.current_question_id not in current_ids:
            return questions[0] if questions else None
        next_index = current_ids.index(session.current_question_id) + 1
        if next_index >= len(questions):
            return None
        return questions[next_index]

    async def _get_session_questions(self, db: AsyncSession, session_id: int) -> list[Question]:
        result = await db.execute(
            select(Question)
            .join(Message, Message.question_id == Question.id)
            .where(Message.session_id == session_id)
            .distinct()
            .order_by(Question.id.asc())
        )
        return list(result.scalars().all())

    async def _safe_evaluate(
        self,
        session: InterviewSession,
        questions: list[Question],
        history: list[Message],
    ) -> LLMEvaluation:
        try:
            return await llm_client.evaluate_interview(session, questions, history)
        except Exception:
            logger.exception("LLM_EVALUATION_FALLBACK_USED session_id=%s", session.id)
            user_answers = [message for message in history if message.sender == MessageSender.USER.value]
            score = min(100.0, 55.0 + len(user_answers) * 8.0)
            return LLMEvaluation(
                score=score,
                correctness=max(0.0, score - 4.0),
                completeness=max(0.0, score - 2.0),
                depth=max(0.0, score - 8.0),
                communication=min(100.0, score + 3.0),
                strengths=["Кандидат дал ответы на часть вопросов интервью."],
                weaknesses=["Оценка сформирована резервным алгоритмом из-за ошибки LLM."],
                recommendations="Проверьте подключение к LLM и повторите интервью для более точной оценки.",
                summary="Резервная оценка без обращения к LLM.",
            )

    async def _safe_generate_follow_up(
        self,
        session: InterviewSession,
        question: Question,
        history: list[Message],
    ) -> LLMInterviewerReply:
        try:
            return await llm_client.generate_interviewer_reply(session, question, history)
        except Exception:
            logger.exception("LLM_INTERVIEWER_FALLBACK_USED session_id=%s question_id=%s", session.id, question.id)
            return LLMInterviewerReply(
                message=(
                    "Уточните, пожалуйста, ответ: какие детали реализации, ограничения и практические примеры "
                    "важны для этого вопроса?"
                ),
                should_ask_follow_up=self._needs_follow_up(history[-1].content if history else ""),
                covered_criteria=[],
                missing_criteria=[],
            )

    def _needs_follow_up(self, content: str) -> bool:
        return len(content.strip()) < 120

    def _resolve_question_limit(
        self,
        requested_count: int | None,
        default_count: int | None,
        available_count: int,
    ) -> int:
        if requested_count is not None:
            if requested_count > MAX_INTERVIEW_QUESTION_COUNT:
                raise ValueError("Количество вопросов в интервью не может превышать 10")
            if requested_count > available_count:
                raise ValueError("Количество вопросов не может превышать доступный банк для выбранного уровня")
            return requested_count

        resolved_default = max(default_count or 1, 1)
        return min(resolved_default, available_count, MAX_INTERVIEW_QUESTION_COUNT)

    def _format_question(self, question: Question, index: int) -> str:
        tags = loads_list(question.tags)
        tag_line = f"\nТемы: {', '.join(tags)}" if tags else ""
        return f"Вопрос {index + 1}: {question.question_text}{tag_line}"


interview_engine = InterviewEngine()
