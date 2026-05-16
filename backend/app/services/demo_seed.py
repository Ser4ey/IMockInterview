from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.interview import (
    ExternalContextSource,
    InterviewResult,
    InterviewSession,
    InterviewStage,
    InterviewStatus,
    Message,
    MessageSender,
    PromptTemplate,
    TariffLimit,
)
from app.models.user import User


DEMO_EMAIL = "demo@imock.dev"
LEGACY_DEMO_EMAIL = "demo@imock.local"
DEMO_PASSWORD = "demo12345"


async def seed_demo_data(db: AsyncSession) -> dict[str, int | str]:
    user = await _get_or_create_demo_user(db)
    await _get_or_create_demo_limit(db, user)
    prompt = await _get_or_create_prompt_template(db)
    source = await _get_or_create_context_source(db)
    await _cleanup_demo_interviews(db, user)
    session = await _get_or_create_showcase_interviews(db, user)
    await db.commit()
    return {
        "email": user.email,
        "password": DEMO_PASSWORD,
        "user_id": user.id,
        "prompt_template_id": prompt.id,
        "context_source_id": source.id,
        "interview_id": session.id,
    }


async def _get_or_create_demo_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
    user = result.scalars().first()
    if user:
        user.hashed_password = get_password_hash(DEMO_PASSWORD)
        user.full_name = "Александр Петров"
        user.role = user.role or "user"
        user.tariff = user.tariff or "free"
        user.is_active = True
        await db.flush()
        return user

    legacy_result = await db.execute(select(User).where(User.email == LEGACY_DEMO_EMAIL))
    legacy_user = legacy_result.scalars().first()
    if legacy_user:
        legacy_user.email = DEMO_EMAIL
        legacy_user.hashed_password = get_password_hash(DEMO_PASSWORD)
        legacy_user.full_name = "Александр Петров"
        legacy_user.role = legacy_user.role or "user"
        legacy_user.tariff = legacy_user.tariff or "free"
        legacy_user.is_active = True
        await db.flush()
        return legacy_user

    user = User(
        email=DEMO_EMAIL,
        hashed_password=get_password_hash(DEMO_PASSWORD),
        full_name="Александр Петров",
        role="user",
        tariff="free",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def _get_or_create_demo_limit(db: AsyncSession, user: User) -> TariffLimit:
    result = await db.execute(select(TariffLimit).where(TariffLimit.user_id == user.id))
    limit = result.scalars().first()
    if limit:
        return limit

    limit = TariffLimit(user_id=user.id, daily_limit=20, used_today=2)
    db.add(limit)
    await db.flush()
    return limit


async def _get_or_create_prompt_template(db: AsyncSession) -> PromptTemplate:
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.interview_type == "full",
            PromptTemplate.level == "Junior",
        )
    )
    prompt = result.scalars().first()
    if prompt:
        prompt.system_prompt = DEMO_SYSTEM_PROMPT
        await db.flush()
        return prompt

    prompt = PromptTemplate(
        interview_type="full",
        level="Junior",
        system_prompt=DEMO_SYSTEM_PROMPT,
    )
    db.add(prompt)
    await db.flush()
    return prompt


async def _get_or_create_context_source(db: AsyncSession) -> ExternalContextSource:
    result = await db.execute(
        select(ExternalContextSource).where(
            ExternalContextSource.specialization == "Python Backend",
            ExternalContextSource.title == "Junior backend baseline",
        )
    )
    source = result.scalars().first()
    if source:
        return source

    source = ExternalContextSource(
        specialization="Python Backend",
        source_type="local",
        title="Junior backend baseline",
        content=(
            "Junior Python Backend: HTTP, REST, основы SQL, транзакции, FastAPI, async basics, "
            "тестирование, простая архитектура, обработка ошибок."
        ),
    )
    db.add(source)
    await db.flush()
    return source


async def _cleanup_demo_interviews(db: AsyncSession, user: User) -> None:
    showcase_keys = {
        ("Python Backend", "Middle", "full"),
        ("REST API и базы данных", "Middle", "theory"),
        ("System Design", "Middle", "technical"),
        ("Backend-разработка / Python", "Middle", "full"),
    }
    result = await db.execute(select(InterviewSession).where(InterviewSession.user_id == user.id))
    for session in result.scalars().all():
        key = (session.specialization, session.level, session.interview_type)
        if key not in showcase_keys:
            await db.delete(session)
    await db.flush()


async def _get_or_create_showcase_interviews(db: AsyncSession, user: User) -> InterviewSession:
    primary = await _get_or_create_demo_interview(
        db=db,
        user=user,
        specialization="Python Backend",
        level="Middle",
        interview_type="full",
        score=85,
        correctness=82,
        completeness=86,
        depth=80,
        communication=90,
        messages=[
            (MessageSender.AI.value, "Расскажите, пожалуйста, как устроена архитектура REST API и какие принципы вы соблюдаете при проектировании эндпоинтов?"),
            (
                MessageSender.USER.value,
                "Я проектирую API с учётом принципов REST: использую ресурсы, HTTP-методы GET, POST, PUT, DELETE, коды статусов, валидацию входных данных и разграничение доступа.",
            ),
            (MessageSender.AI.value, "Хорошо. А как бы вы спроектировали пагинацию для большого списка данных?"),
            (
                MessageSender.USER.value,
                "Для простых списков использовал бы limit и offset, а для высоких нагрузок предпочел бы cursor-based пагинацию, чтобы избежать проблем с большими смещениями.",
            ),
        ],
        recommendations=(
            "Кандидат уверенно объясняет REST-подход и хорошо структурирует ответы. "
            "Для дальнейшего роста стоит глубже раскрывать trade-off между offset и cursor-based пагинацией, "
            "а также чаще приводить примеры из реальных проектов."
        ),
    )
    await _get_or_create_demo_interview(
        db=db,
        user=user,
        specialization="REST API и базы данных",
        level="Middle",
        interview_type="theory",
        score=80,
        correctness=78,
        completeness=82,
        depth=76,
        communication=84,
        messages=[
            (MessageSender.AI.value, "Объясните, зачем нужны индексы в базе данных и когда они могут навредить."),
            (MessageSender.USER.value, "Индексы ускоряют поиск, но замедляют запись и занимают место. Их важно подбирать под реальные запросы."),
        ],
        recommendations="Хорошая база по SQL. Рекомендуется повторить планы выполнения запросов и составные индексы.",
    )
    await _get_or_create_demo_interview(
        db=db,
        user=user,
        specialization="System Design",
        level="Middle",
        interview_type="technical",
        score=70,
        correctness=72,
        completeness=68,
        depth=66,
        communication=74,
        messages=[
            (MessageSender.AI.value, "Как бы вы спроектировали сервис уведомлений для большого количества пользователей?"),
            (MessageSender.USER.value, "Я бы выделил очередь событий, воркеры отправки, retry-механику и хранение статусов доставки."),
        ],
        recommendations="Стоит подробнее раскрывать масштабирование, отказоустойчивость и мониторинг фоновых задач.",
    )
    await _get_or_create_active_demo_interview(db, user)
    return primary


async def _get_or_create_demo_interview(
    db: AsyncSession,
    user: User,
    specialization: str,
    level: str,
    interview_type: str,
    score: int,
    correctness: int,
    completeness: int,
    depth: int,
    communication: int,
    messages: list[tuple[str, str]],
    recommendations: str,
) -> InterviewSession:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.user_id == user.id,
            InterviewSession.specialization == specialization,
            InterviewSession.level == level,
            InterviewSession.interview_type == interview_type,
        )
    )
    session = result.scalars().first()
    if session:
        existing_result = await db.execute(select(InterviewResult).where(InterviewResult.session_id == session.id))
        interview_result = existing_result.scalars().first()
        if interview_result:
            interview_result.score = score
            interview_result.correctness = correctness
            interview_result.completeness = completeness
            interview_result.depth = depth
            interview_result.communication = communication
            interview_result.recommendations = recommendations
        session.status = InterviewStatus.FINISHED.value
        session.stage = InterviewStage.FINISHED.value
        await db.flush()
        return session

    session = InterviewSession(
        user_id=user.id,
        specialization=specialization,
        level=level,
        interview_type=interview_type,
        status=InterviewStatus.FINISHED.value,
        stage=InterviewStage.FINISHED.value,
    )
    db.add(session)
    await db.flush()

    db.add_all([Message(session_id=session.id, sender=sender, content=content) for sender, content in messages])
    db.add(
        InterviewResult(
            session_id=session.id,
            score=score,
            correctness=correctness,
            completeness=completeness,
            depth=depth,
            communication=communication,
            recommendations=recommendations,
        )
    )
    await db.flush()
    return session


async def _get_or_create_active_demo_interview(db: AsyncSession, user: User) -> InterviewSession:
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.user_id == user.id,
            InterviewSession.specialization == "Backend-разработка / Python",
            InterviewSession.level == "Middle",
            InterviewSession.interview_type == "full",
            InterviewSession.status == InterviewStatus.ACTIVE.value,
        )
    )
    session = result.scalars().first()
    if session:
        session.stage = InterviewStage.TECHNICAL.value
        await db.flush()
        return session

    session = InterviewSession(
        user_id=user.id,
        specialization="Backend-разработка / Python",
        level="Middle",
        interview_type="full",
        status=InterviewStatus.ACTIVE.value,
        stage=InterviewStage.TECHNICAL.value,
    )
    db.add(session)
    await db.flush()

    db.add_all(
        [
            Message(
                session_id=session.id,
                sender=MessageSender.AI.value,
                content="Расскажите, пожалуйста, как устроена архитектура REST API и какие принципы вы соблюдаете при проектировании эндпоинтов?",
            ),
            Message(
                session_id=session.id,
                sender=MessageSender.USER.value,
                content="Я проектирую API с учётом принципов REST: использую ресурсы, HTTP-методы GET, POST, PUT, DELETE, коды статусов, валидацию входных данных и разграничение доступа.",
            ),
            Message(
                session_id=session.id,
                sender=MessageSender.AI.value,
                content="Хорошо. А как бы вы спроектировали пагинацию для большого списка данных?",
            ),
        ]
    )
    await db.flush()
    return session


DEMO_SYSTEM_PROMPT = (
    "Проведи mock-собеседование на русском языке. "
    "Соблюдай этапы: самопрезентация, технические вопросы, практика, soft skills, обратная связь."
)
