from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    InterviewResult,
    InterviewSession,
    InterviewStage,
    InterviewStatus,
    InterviewType,
    Message,
    MessageSender,
)
from app.schemas.interview import InterviewSessionCreate
from app.services.llm_client import LLMEvaluation, llm_client


STAGE_FLOW: dict[InterviewType, list[InterviewStage]] = {
    InterviewType.FULL: [
        InterviewStage.INTRO,
        InterviewStage.SELF_PRESENTATION,
        InterviewStage.TECHNICAL,
        InterviewStage.PRACTICE,
        InterviewStage.SOFT_SKILLS,
        InterviewStage.FEEDBACK,
        InterviewStage.FINISHED,
    ],
    InterviewType.THEORY: [
        InterviewStage.INTRO,
        InterviewStage.TECHNICAL,
        InterviewStage.FEEDBACK,
        InterviewStage.FINISHED,
    ],
    InterviewType.SELF_PRESENTATION: [
        InterviewStage.INTRO,
        InterviewStage.SELF_PRESENTATION,
        InterviewStage.FEEDBACK,
        InterviewStage.FINISHED,
    ],
    InterviewType.TECHNICAL: [
        InterviewStage.INTRO,
        InterviewStage.TECHNICAL,
        InterviewStage.PRACTICE,
        InterviewStage.FEEDBACK,
        InterviewStage.FINISHED,
    ],
}


class InterviewEngine:
    async def create_session(
        self,
        db: AsyncSession,
        user_id: int,
        interview_in: InterviewSessionCreate,
    ) -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            specialization=interview_in.specialization,
            level=interview_in.level,
            interview_type=interview_in.interview_type.value,
            stage=InterviewStage.INTRO.value,
        )
        db.add(session)
        await db.flush()
        db.add(
            Message(
                session_id=session.id,
                sender=MessageSender.AI.value,
                content=self._prompt_for_stage(session, InterviewStage.INTRO),
            )
        )
        await db.commit()
        await db.refresh(session)
        return session

    async def submit_user_answer(
        self,
        db: AsyncSession,
        session: InterviewSession,
        content: str,
    ) -> tuple[InterviewSession, list[Message], InterviewResult | None]:
        if session.status == InterviewStatus.FINISHED.value:
            raise ValueError("Собеседование уже завершено")

        user_message = Message(session_id=session.id, sender=MessageSender.USER.value, content=content)
        db.add(user_message)
        await db.flush()

        next_stage = self._next_stage(session)
        session.stage = next_stage.value

        if next_stage == InterviewStage.FINISHED:
            result = await self._finish_session(db, session)
            ai_content = "Собеседование завершено. Я подготовил итоговую оценку и рекомендации."
            ai_sender = MessageSender.AI.value
        else:
            result = None
            history = await self._get_messages(db, session.id)
            ai_content, ai_sender = await self._safe_generate_stage_prompt(session, next_stage, history)

        ai_message = Message(session_id=session.id, sender=ai_sender, content=ai_content)
        db.add(ai_message)
        await db.commit()
        await db.refresh(session)
        await db.refresh(user_message)
        await db.refresh(ai_message)
        if result:
            await db.refresh(result)
        return session, [user_message, ai_message], result

    async def finish_session(
        self,
        db: AsyncSession,
        session: InterviewSession,
    ) -> tuple[InterviewSession, InterviewResult]:
        if session.status != InterviewStatus.FINISHED.value:
            session.stage = InterviewStage.FINISHED.value
            result = await self._finish_session(db, session)
            db.add(
                Message(
                    session_id=session.id,
                    sender=MessageSender.AI.value,
                    content="Собеседование завершено досрочно. Итог сформирован по уже полученным ответам.",
                )
            )
            await db.commit()
            await db.refresh(session)
            await db.refresh(result)
            return session, result

        result = await self._get_or_create_result(db, session)
        await db.commit()
        await db.refresh(session)
        await db.refresh(result)
        return session, result

    def _next_stage(self, session: InterviewSession) -> InterviewStage:
        flow = STAGE_FLOW[InterviewType(session.interview_type)]
        current = InterviewStage(session.stage)
        current_index = flow.index(current)
        return flow[min(current_index + 1, len(flow) - 1)]

    def _prompt_for_stage(self, session: InterviewSession, stage: InterviewStage) -> str:
        prompts = {
            InterviewStage.INTRO: (
                f"Здравствуйте! Начинаем mock-собеседование: {session.specialization}, уровень {session.level}. "
                "Напишите, что вы готовы начать, и кратко обозначьте свой опыт."
            ),
            InterviewStage.SELF_PRESENTATION: (
                "Блок самопрезентации. Расскажите о себе, опыте, ключевых проектах и вашей роли в них."
            ),
            InterviewStage.TECHNICAL: (
                f"Технический блок. Объясните одну важную тему из области {session.specialization}: "
                "как она работает, где применяется и какие у нее есть ограничения."
            ),
            InterviewStage.PRACTICE: (
                "Практический блок. Опишите, как бы вы спроектировали небольшое решение для реальной задачи: "
                "архитектура, данные, проверки, риски."
            ),
            InterviewStage.SOFT_SKILLS: (
                "Блок soft skills. Расскажите о сложной рабочей ситуации, конфликте или дедлайне: "
                "что произошло, что вы сделали и какой был результат."
            ),
            InterviewStage.FEEDBACK: "Финальный блок. Есть ли что-то, что вы хотите добавить перед итоговой оценкой?",
        }
        return prompts[stage]

    async def _finish_session(self, db: AsyncSession, session: InterviewSession) -> InterviewResult:
        session.status = InterviewStatus.FINISHED.value
        session.finished_at = datetime.now(timezone.utc)
        return await self._get_or_create_result(db, session)

    async def _get_or_create_result(self, db: AsyncSession, session: InterviewSession) -> InterviewResult:
        result = await db.execute(select(InterviewResult).where(InterviewResult.session_id == session.id))
        existing = result.scalars().first()
        if existing:
            return existing

        history = await self._get_messages(db, session.id)
        evaluation = await self._safe_evaluate(session, history)
        interview_result = InterviewResult(
            session_id=session.id,
            score=evaluation.score,
            correctness=evaluation.correctness,
            completeness=evaluation.completeness,
            depth=evaluation.depth,
            communication=evaluation.communication,
            recommendations=evaluation.recommendations,
        )
        db.add(interview_result)
        await db.flush()
        return interview_result

    async def _get_messages(self, db: AsyncSession, session_id: int) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(result.scalars().all())

    async def _safe_evaluate(self, session: InterviewSession, history: list[Message]) -> LLMEvaluation:
        try:
            return await llm_client.evaluate_interview(session, history)
        except Exception:
            user_answers = [message for message in history if message.sender == MessageSender.USER.value]
            score = min(100.0, 50.0 + len(user_answers) * 10.0)
            return LLMEvaluation(
                score=score,
                correctness=min(100.0, score),
                completeness=min(100.0, score),
                depth=max(0.0, score - 5.0),
                communication=min(100.0, score + 5.0),
                recommendations="Оценка сформирована локальным резервным алгоритмом из-за ошибки LLM.",
            )

    async def _safe_generate_stage_prompt(
        self,
        session: InterviewSession,
        stage: InterviewStage,
        history: list[Message],
    ) -> tuple[str, str]:
        try:
            return await llm_client.generate_stage_prompt(session, stage, history), MessageSender.AI.value
        except Exception:
            return (
                "Не удалось получить ответ AI-интервьюера. Проверьте подключение к AI-сервису или повторите попытку позже.",
                MessageSender.SYSTEM.value,
            )


interview_engine = InterviewEngine()
