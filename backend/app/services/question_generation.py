from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    InterviewType,
    Question,
    QuestionGenerationJob,
    QuestionGenerationStatus,
    QuestionSource,
)
from app.services.llm_client import GeneratedQuestion, llm_client
from app.services.question_quality import build_question_hash, normalize_question_text, validate_generated_question
from app.services.serialization import dumps_list


class QuestionGenerationService:
    async def generate_questions(
        self,
        db: AsyncSession,
        interview_type: InterviewType,
        level: str,
        requested_count: int,
    ) -> QuestionGenerationJob:
        job = QuestionGenerationJob(
            interview_type_id=interview_type.id,
            level=level,
            requested_count=requested_count,
            status=QuestionGenerationStatus.RUNNING.value,
        )
        db.add(job)
        await db.flush()

        try:
            job.provider = getattr(llm_client, "provider", "mock")
            generated = await llm_client.generate_question_bank(interview_type, level, requested_count)
            saved_count = await self._save_generated_questions(
                db,
                interview_type,
                level,
                generated,
                job.provider,
            )
            job.status = QuestionGenerationStatus.COMPLETED.value
            job.generated_count = saved_count
            job.skipped_count = max(0, len(generated) - saved_count)
            job.context_used = job.provider == "yandex_agent" and any(item.source_title or item.source_url for item in generated)
            job.input_tokens = getattr(llm_client, "input_tokens", 0)
            job.output_tokens = getattr(llm_client, "output_tokens", 0)
            job.finished_at = datetime.now(timezone.utc)
        except Exception as exc:
            job.status = QuestionGenerationStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)

        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def _save_generated_questions(
        self,
        db: AsyncSession,
        interview_type: InterviewType,
        level: str,
        generated: list[GeneratedQuestion],
        provider: str = "mock",
    ) -> int:
        saved_count = 0
        seen_hashes: set[str] = set()
        for item in generated:
            if validate_generated_question(item, level):
                continue

            question_hash = build_question_hash(interview_type.id, level, item.question_text)
            if question_hash in seen_hashes:
                continue
            seen_hashes.add(question_hash)
            if await self._question_exists(db, interview_type.id, level, item.question_text, question_hash):
                continue

            source = QuestionSource(
                title=item.source_title or "LLM generation",
                url=item.source_url,
                source_type="agent" if provider == "yandex_agent" else "llm",
                retrieved_at=datetime.now(timezone.utc),
            )
            db.add(source)
            await db.flush()
            db.add(
                Question(
                    interview_type_id=interview_type.id,
                    level=level,
                    question_text=item.question_text,
                    expected_answer=item.expected_answer,
                    evaluation_criteria=dumps_list(item.evaluation_criteria),
                    tags=dumps_list(item.tags),
                    question_hash=question_hash,
                    source_id=source.id,
                    is_active=True,
                )
            )
            saved_count += 1
        await db.flush()
        return saved_count

    async def _question_exists(
        self,
        db: AsyncSession,
        interview_type_id: int,
        level: str,
        question_text: str,
        question_hash: str,
    ) -> bool:
        result = await db.execute(
            select(Question).where(
                Question.interview_type_id == interview_type_id,
                Question.level == level,
            )
        )
        normalized_candidate = normalize_question_text(question_text)
        for existing in result.scalars().all():
            if existing.question_hash == question_hash:
                return True
            if normalize_question_text(existing.question_text) == normalized_candidate:
                return True
        return False


question_generation_service = QuestionGenerationService()
