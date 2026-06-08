from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.interview import (
    InterviewResult,
    InterviewSession,
    InterviewStage,
    InterviewStatus,
    InterviewType,
    Message,
    MessageSender,
    PromptTemplate,
    Question,
    QuestionSource,
    UsageLimit,
)
from app.models.user import User
from app.services.question_quality import build_question_hash
from app.services.serialization import dumps_list


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "user@example.com"
USER_PASSWORD = "user123"


async def seed_demo_data(db: AsyncSession) -> dict[str, int | str]:
    admin = await _upsert_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, "Администратор IMock", "admin", True)
    user = await _upsert_user(db, USER_EMAIL, USER_PASSWORD, "Иван Кандидат", "user", False)
    await _upsert_usage_limit(db, user)
    await _upsert_prompt_template(db)

    backend = await _upsert_interview_type(
        db,
        title="Backend Java-разработчик",
        role="Backend Java-разработчик",
        technology_stack="Java, Spring Boot, SQL, REST API, микросервисы",
        description="Техническое mock-собеседование для backend-разработчиков Java.",
    )
    frontend = await _upsert_interview_type(
        db,
        title="Frontend React-разработчик",
        role="Frontend React-разработчик",
        technology_stack="React, TypeScript, JavaScript, REST API, UI architecture",
        description="Mock-собеседование по frontend-разработке на React.",
    )
    await _seed_questions(db, backend, BACKEND_JAVA_QUESTIONS)
    await _seed_questions(db, frontend, FRONTEND_REACT_QUESTIONS)
    showcase_session = await _seed_showcase_interview(db, user, backend)

    await db.commit()
    return {
        "admin_email": admin.email,
        "admin_password": ADMIN_PASSWORD,
        "user_email": user.email,
        "user_password": USER_PASSWORD,
        "backend_type_id": backend.id,
        "frontend_type_id": frontend.id,
        "interview_id": showcase_session.id,
    }


async def _upsert_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    role: str,
    is_superuser: bool,
) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email)
        db.add(user)
    user.hashed_password = get_password_hash(password)
    user.full_name = full_name
    user.role = role
    user.is_superuser = is_superuser
    user.is_active = True
    await db.flush()
    return user


async def _upsert_usage_limit(db: AsyncSession, user: User) -> UsageLimit:
    limit = await db.scalar(select(UsageLimit).where(UsageLimit.user_id == user.id))
    if not limit:
        limit = UsageLimit(user_id=user.id, daily_limit=20, used_today=0)
        db.add(limit)
    await db.flush()
    return limit


async def _upsert_prompt_template(db: AsyncSession) -> PromptTemplate:
    prompt = await db.scalar(select(PromptTemplate).where(PromptTemplate.name == "default-interviewer"))
    if not prompt:
        prompt = PromptTemplate(name="default-interviewer", purpose="interview", system_prompt=DEMO_SYSTEM_PROMPT)
        db.add(prompt)
    else:
        prompt.system_prompt = DEMO_SYSTEM_PROMPT
        prompt.is_active = True
    await db.flush()
    return prompt


async def _upsert_interview_type(
    db: AsyncSession,
    title: str,
    role: str,
    technology_stack: str,
    description: str,
) -> InterviewType:
    item = await db.scalar(select(InterviewType).where(InterviewType.title == title))
    if not item:
        item = InterviewType(title=title)
        db.add(item)
    item.role = role
    item.technology_stack = technology_stack
    item.description = description
    item.levels = dumps_list(["junior", "middle", "senior"])
    item.default_question_count = 3
    item.is_active = True
    await db.flush()
    return item


async def _seed_questions(
    db: AsyncSession,
    interview_type: InterviewType,
    questions_by_level: dict[str, list[dict[str, object]]],
) -> None:
    await db.execute(delete(Question).where(Question.interview_type_id == interview_type.id))
    source = QuestionSource(
        title=f"Seed: {interview_type.title}",
        url=None,
        source_type="seed",
    )
    db.add(source)
    await db.flush()
    for level, questions in questions_by_level.items():
        for question in questions:
            db.add(
                Question(
                    interview_type_id=interview_type.id,
                    level=level,
                    question_text=str(question["question_text"]),
                    expected_answer=str(question["expected_answer"]),
                    evaluation_criteria=dumps_list(list(question["evaluation_criteria"])),
                    tags=dumps_list(list(question["tags"])),
                    question_hash=build_question_hash(interview_type.id, level, str(question["question_text"])),
                    source_id=source.id,
                    is_active=True,
                )
            )
    await db.flush()


async def _seed_showcase_interview(db: AsyncSession, user: User, interview_type: InterviewType) -> InterviewSession:
    existing_sessions = await db.execute(select(InterviewSession.id).where(InterviewSession.user_id == user.id))
    session_ids = [row[0] for row in existing_sessions.all()]
    if session_ids:
        await db.execute(delete(InterviewResult).where(InterviewResult.session_id.in_(session_ids)))
        await db.execute(delete(Message).where(Message.session_id.in_(session_ids)))
        await db.execute(delete(InterviewSession).where(InterviewSession.id.in_(session_ids)))
        await db.flush()
    first_question = await db.scalar(
        select(Question)
        .where(
            Question.interview_type_id == interview_type.id,
            Question.level == "middle",
            Question.is_active.is_(True),
        )
        .order_by(Question.id.asc())
    )
    session = InterviewSession(
        user_id=user.id,
        interview_type_id=interview_type.id,
        level="middle",
        status=InterviewStatus.FINISHED.value,
        stage=InterviewStage.FINISHED.value,
        current_question_id=first_question.id if first_question else None,
        question_index=1,
    )
    db.add(session)
    await db.flush()
    if first_question:
        db.add_all(
            [
                Message(
                    session_id=session.id,
                    question_id=first_question.id,
                    sender=MessageSender.AI.value,
                    content=f"Вопрос 1: {first_question.question_text}",
                ),
                Message(
                    session_id=session.id,
                    question_id=first_question.id,
                    sender=MessageSender.USER.value,
                    content=(
                        "Spring IoC container создаёт и связывает beans, управляет их жизненным циклом, "
                        "внедряет зависимости и позволяет отделить бизнес-логику от конкретных реализаций."
                    ),
                ),
            ]
        )
    db.add(
        InterviewResult(
            session_id=session.id,
            score=86,
            correctness=84,
            completeness=86,
            depth=82,
            communication=90,
            strengths=dumps_list([
                "Кандидат уверенно объясняет роль IoC и dependency injection.",
                "Ответ структурирован и связан с практикой Spring Boot.",
            ]),
            weaknesses=dumps_list([
                "Стоит подробнее раскрыть lifecycle beans и scopes.",
                "Полезно добавить пример proxy-механики на @Transactional.",
            ]),
            recommendations=(
                "Повторите жизненный цикл Spring beans, scopes, proxy-based AOP и транзакции. "
                "На интервью добавляйте примеры из реальных сервисов."
            ),
            summary="Демонстрационное middle-интервью по Backend Java сохранено для истории и прогресса.",
        )
    )
    await db.flush()
    return session


DEMO_SYSTEM_PROMPT = (
    "Проводи mock-собеседование на русском языке. Используй только вопросы из банка, "
    "эталонные ответы и критерии оценки. Задавай уточнения, если ответ неполный."
)


BACKEND_JAVA_QUESTIONS = {
    "junior": [
        {
            "question_text": "Чем отличается ArrayList от LinkedList в Java?",
            "expected_answer": "Нужно сравнить структуру хранения, сложность доступа, вставки и удаления, а также реальные сценарии применения.",
            "evaluation_criteria": ["структуры данных", "сложность операций", "практический выбор коллекции"],
            "tags": ["Java", "Collections"],
        },
        {
            "question_text": "Что такое интерфейс в Java?",
            "expected_answer": "Интерфейс задаёт контракт поведения, поддерживает полиморфизм и позволяет отделить реализацию от использования.",
            "evaluation_criteria": ["ООП", "контракт", "полиморфизм"],
            "tags": ["Java", "OOP"],
        },
        {
            "question_text": "Что такое REST API?",
            "expected_answer": "Кандидат должен объяснить ресурсы, HTTP-методы, коды статусов, stateless-взаимодействие и формат обмена.",
            "evaluation_criteria": ["REST", "HTTP", "stateless"],
            "tags": ["REST", "Backend"],
        },
    ],
    "middle": [
        {
            "question_text": "Как работает Spring IoC container?",
            "expected_answer": "Нужно описать IoC, DI, beans, lifecycle, scopes и конфигурацию application context.",
            "evaluation_criteria": ["IoC", "DI", "bean lifecycle", "scopes"],
            "tags": ["Java", "Spring"],
        },
        {
            "question_text": "Чем optimistic locking отличается от pessimistic locking?",
            "expected_answer": "Нужно сравнить версионность и блокировки, влияние на конкуренцию, производительность и сценарии применения.",
            "evaluation_criteria": ["конкурентный доступ", "version column", "locks", "trade-offs"],
            "tags": ["Database", "Transactions"],
        },
        {
            "question_text": "Как устроена обработка транзакций в Spring?",
            "expected_answer": "Кандидат раскрывает @Transactional, propagation, isolation, rollback rules и proxy-based механику.",
            "evaluation_criteria": ["@Transactional", "isolation", "propagation", "rollback"],
            "tags": ["Spring", "Transactions"],
        },
    ],
    "senior": [
        {
            "question_text": "Как спроектировать отказоустойчивый сервис обработки заказов?",
            "expected_answer": "Нужно раскрыть очереди, идемпотентность, outbox, retry, мониторинг, деградацию и восстановление.",
            "evaluation_criteria": ["fault tolerance", "idempotency", "outbox", "observability"],
            "tags": ["Architecture", "Reliability"],
        },
        {
            "question_text": "Как диагностировать деградацию производительности backend-сервиса?",
            "expected_answer": "Кандидат описывает метрики, tracing, profiling, БД, пулы, очереди и внешние зависимости.",
            "evaluation_criteria": ["metrics", "tracing", "profiling", "root cause"],
            "tags": ["Performance", "Backend"],
        },
        {
            "question_text": "Какие компромиссы есть у микросервисной архитектуры?",
            "expected_answer": "Нужно сравнить независимую поставку, границы сервисов, консистентность данных, сеть и эксплуатационную сложность.",
            "evaluation_criteria": ["service boundaries", "distributed systems", "data consistency", "operations"],
            "tags": ["Microservices", "Architecture"],
        },
    ],
}


FRONTEND_REACT_QUESTIONS = {
    "junior": [
        {
            "question_text": "Чем props отличаются от state в React?",
            "expected_answer": "Props приходят от родителя и считаются входными данными, state хранится внутри компонента и меняется через setState/useState.",
            "evaluation_criteria": ["props", "state", "data flow"],
            "tags": ["React", "Basics"],
        },
        {
            "question_text": "Зачем нужен useEffect?",
            "expected_answer": "useEffect используется для сайд-эффектов, подписок, загрузки данных и cleanup при изменении зависимостей.",
            "evaluation_criteria": ["side effects", "dependencies", "cleanup"],
            "tags": ["React", "Hooks"],
        },
        {
            "question_text": "Что такое controlled component?",
            "expected_answer": "Это компонент формы, значение которого хранится в React state и обновляется через обработчики событий.",
            "evaluation_criteria": ["forms", "state", "controlled input"],
            "tags": ["React", "Forms"],
        },
    ],
    "middle": [
        {
            "question_text": "Как избежать лишних ререндеров в React-приложении?",
            "expected_answer": "Нужно упомянуть структуру state, memo, useMemo, useCallback, ключи списков и профилирование.",
            "evaluation_criteria": ["render model", "memoization", "profiling"],
            "tags": ["React", "Performance"],
        },
        {
            "question_text": "Как организовать работу с серверным состоянием во frontend?",
            "expected_answer": "Кандидат раскрывает кеширование, invalidation, loading/error states, optimistic updates и синхронизацию.",
            "evaluation_criteria": ["server state", "cache", "invalidation", "UX states"],
            "tags": ["Frontend", "API"],
        },
        {
            "question_text": "Какие риски есть при загрузке данных внутри useEffect?",
            "expected_answer": "Нужно назвать race conditions, abort controller, повторные запросы, stale state и обработку ошибок.",
            "evaluation_criteria": ["async effects", "race conditions", "error handling"],
            "tags": ["React", "Hooks"],
        },
    ],
    "senior": [
        {
            "question_text": "Как спроектировать frontend-архитектуру большого React-приложения?",
            "expected_answer": "Нужно раскрыть модульные границы, routing, state management, дизайн-систему, тесты и delivery.",
            "evaluation_criteria": ["architecture", "module boundaries", "state management", "testing"],
            "tags": ["React", "Architecture"],
        },
        {
            "question_text": "Как выстроить стратегию производительности для сложного интерфейса?",
            "expected_answer": "Кандидат говорит о Web Vitals, profiling, code splitting, lazy loading, render optimization и UX budgets.",
            "evaluation_criteria": ["Web Vitals", "bundle", "render performance", "profiling"],
            "tags": ["Frontend", "Performance"],
        },
        {
            "question_text": "Как обеспечить качество frontend-продукта в команде?",
            "expected_answer": "Нужно описать тестовую пирамиду, code review, дизайн-систему, мониторинг и процессы релиза.",
            "evaluation_criteria": ["quality", "testing", "code review", "monitoring"],
            "tags": ["Frontend", "Engineering"],
        },
    ],
}
