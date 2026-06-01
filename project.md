# IMock: план очистки и финальной доработки проекта

## Статус выполнения

Обновляется по мере реализации.

- [x] Этап 0. Базовая фиксация состояния.
- [x] Этап 1. Удаление legacy chat-ветки.
- [x] Этап 2. Очистка LLM-слоя и провайдера YandexGPT.
- [x] Этап 3. Модели БД для типов интервью и банка вопросов.
- [x] Этап 4. Admin API.
- [x] Этап 5. Публичный API типов интервью.
- [x] Этап 6. Генерация банка вопросов.
- [x] Этап 7. Новый сценарий проведения интервью.
- [x] Этап 8. Структурированный результат и прогресс.
- [x] Этап 9. Seed-данные для защиты.
- [x] Этап 10. Admin UI.
- [x] Этап 11. Пользовательский frontend flow.
- [x] Этап 12. Удаление коммерческой логики и финальная терминология.
- [x] Этап 13. README и документация для защиты.
- [x] Этап 14. Полная проверка качества.
- [x] Этап 15. Финальный демонстрационный сценарий.

### Журнал выполнения

- 2026-05-24: старт реализации по плану. Сначала выполняется очистка legacy-кода, затем новые модели, API, UI, seed, тесты и документация.
- 2026-05-24: backend переведён на чистую архитектуру `/interviews`: legacy `/chats` удалён, добавлены `InterviewType`, `Question`, `QuestionSource`, `QuestionGenerationJob`, единый LLM-клиент, admin API, публичный API типов интервью, question generation service и новый interview engine на базе банка вопросов. Проверка: `python -m unittest discover -s tests` - 8 тестов OK.
- 2026-05-24: frontend переведён на каталог типов интервью из БД, добавлены страницы администратора `/admin/interview-types`, `/admin/questions`, `/admin/question-generation-jobs`, удалены legacy routes `/chats/*`. Проверка: `npm run build` - OK.
- 2026-05-24: README и `architecture.md` переписаны под финальный сценарий ВКР. Финальные проверки: backend `python -m unittest discover -s tests` - OK, frontend `npm run build` - OK, seed `python .\scripts\seed_demo.py` - OK, e2e `npm run test:e2e` - OK. Поиск legacy/commercial терминов в исходниках `backend/app`, `frontend/src`, `backend/tests`, `backend/alembic` - без совпадений.
- 2026-05-24: runtime-артефакты очищены из рабочей папки и git index: `__pycache__`, `.pyc`, локальные логи, pid/failure-файлы и SQLite-база.

## Цель

Привести IMock к чистому финальному состоянию для защиты ВКР по теме "Веб-сервис для проведения Mock-собеседований на основе ИИ".

На выходе проект должен быть специализированной системой mock-собеседований, а не обычным AI-чатом:

- пользователь выбирает тип собеседования и уровень;
- администратор управляет типами собеседований и банком вопросов;
- вопросы заранее сохраняются в базе данных;
- AI-интервьюер работает с вопросом, эталонным ответом и критериями оценки;
- сохраняются сессии, сообщения, результаты, история и прогресс;
- отсутствует коммерческая логика: тарифы, подписки, оплаты, Free/Pro/Premium.

## Текущее состояние проекта

### Стек

- Backend: FastAPI, Python, async SQLAlchemy, SQLite, Alembic, Pydantic, JWT.
- Frontend: React, TypeScript, Vite, Material UI.
- LLM: есть mock-режим и интеграция с YandexGPT, но слой сейчас частично дублируется.
- БД: SQLite для локального запуска и демонстрации.

### Что уже есть

- Регистрация и вход по JWT.
- Роли пользователя через поля `role` и `is_superuser`.
- Пользовательские интервью через `/api/v1/interviews`.
- Сообщения и результаты интервью.
- Прогресс пользователя.
- Технические лимиты запросов к AI.
- Mock LLM и YandexGPT-клиент.
- Демо-seed.
- Backend-тесты и frontend build.

### Что нужно заменить или удалить

В проекте есть legacy-ветка чатов, которая дублирует смысл интервью и мешает чистой архитектуре:

- `backend/app/models/chat.py`;
- `backend/app/schemas/chat.py`;
- `backend/app/repositories/chat_repository.py`;
- `backend/app/services/interview_service.py`;
- `backend/app/api/endpoints/chats.py`;
- `frontend/src/api/chats.ts`;
- `frontend/src/types/chat.ts`;
- frontend routes `/chats/:id` и `/chats/:id/result`;
- тесты, которые проверяют legacy chat lifecycle.

Также есть дублирующий LLM-код:

- `backend/app/services/yandex_gpt.py` дублирует часть `backend/app/services/llm_client.py`.

Legacy-код нужно вырезать после того, как основной сценарий `/interviews` будет готов покрыть нужную функциональность.

## Принципы работы

1. Не переписывать весь проект за один раз.
2. Каждый этап должен завершаться локальной проверкой.
3. Если после этапа тесты падают, сначала исправить регрессию, потом идти дальше.
4. Удалять legacy-код смело, но только когда новый путь уже покрывает нужный сценарий.
5. Не хранить API-ключи в коде.
6. Не добавлять коммерческую модель.
7. Для frontend соблюдать стиль Nordic Studio из `docs/design-nordic-studio.md`.
8. Для запуска серверов использовать только конечные orchestration-скрипты, не foreground `npm run dev` и не foreground `uvicorn`.

## Этап 0. Базовая фиксация состояния

### Работы

- Проверить текущее рабочее дерево.
- Зафиксировать список уже изменённых файлов и артефактов.
- Отделить файлы, которые реально относятся к проекту, от логов, `.pyc`, SQLite-базы, screenshots и временных pid-файлов.
- Убедиться, что `.gitignore` закрывает мусорные артефакты:
  - `__pycache__/`;
  - `*.pyc`;
  - `backend/imock.db`;
  - `*.log`;
  - `.vkr_*.pid`;
  - `frontend/dist/`;
  - `node_modules/`;
  - Python venv.

### Файлы

- `.gitignore`;
- `work-logs.md`;
- возможно служебные docs, если они мешают чистоте проекта.

### Проверка

- `git status --short`.
- Убедиться, что мусорные runtime-файлы больше не попадают в список новых изменений.

### Критерий готовности

Понятно, какие файлы являются исходным кодом и документацией, а какие являются локальными артефактами.

## Этап 1. Удаление legacy chat-ветки

### Работы

- Удалить legacy backend chat API.
- Удалить legacy chat models, schemas и repositories.
- Убрать импорт `chats` из `backend/app/api/api.py`.
- Убрать `Chat` и `ChatMessage` из `backend/app/db/base.py`.
- Удалить frontend API и типы для legacy chats.
- Удалить routes `/chats/:id` и `/chats/:id/result`.
- Удалить или переписать тесты, которые проверяют `/api/v1/chats`.
- Проверить, что пользовательский сценарий идет только через `/api/v1/interviews`.

### Файлы для удаления

- `backend/app/models/chat.py`;
- `backend/app/schemas/chat.py`;
- `backend/app/repositories/chat_repository.py`;
- `backend/app/services/interview_service.py`;
- `backend/app/api/endpoints/chats.py`;
- `frontend/src/api/chats.ts`;
- `frontend/src/types/chat.ts`.

### Файлы для изменения

- `backend/app/api/api.py`;
- `backend/app/db/base.py`;
- `frontend/src/App.tsx`;
- `backend/tests/test_stage10_endpoint_contracts.py`;
- возможно другие backend/frontend тесты, если они импортируют chat-слой.

### Проверка

- `rg -n "chats|Chat|chat_repo|interview_service|/chats" backend frontend`.
- `python -m unittest discover -s tests` из `backend`.
- `npm run build` из `frontend`.

### Критерий готовности

В проекте нет второй параллельной реализации интервью через chat. Основной путь один: `/interviews`.

## Этап 2. Очистка LLM-слоя и провайдера YandexGPT

### Работы

- Оставить единый LLM-слой через `BaseLLMClient`.
- Удалить или слить `YandexGPTService` из `yandex_gpt.py` в `llm_client.py`.
- Добавить единые методы:
  - генерация следующей реплики интервьюера;
  - оценка ответа на конкретный вопрос;
  - итоговая оценка интервью;
  - генерация банка вопросов.
- Добавить нормальное логирование технических ошибок.
- Проверить конфигурацию через env:
  - `LLM_MODE=mock`;
  - `LLM_MODE=yandex`;
  - `YANDEX_FOLDER_ID`;
  - `YANDEX_API_KEY`;
  - timeout.
- Mock-режим должен работать без внешних ключей.

### Файлы

- `backend/app/services/llm_client.py`;
- `backend/app/services/prompt_builder.py`;
- `backend/app/core/config.py`;
- удалить `backend/app/services/yandex_gpt.py`, если после слияния он больше не нужен;
- `backend/.env.example`;
- backend tests для LLM.

### Проверка

- `rg -n "YandexGPTService|yandex_gpt|AIService|generate_interview_questions|conduct_interview_step" backend/app backend/tests`.
- `python -m unittest discover -s tests`.

### Критерий готовности

В проекте один понятный LLM abstraction layer, без дублирующих сервисов.

## Этап 3. Модели БД для типов интервью и банка вопросов

### Работы

- Добавить сущность типа собеседования.
- Избежать конфликта с текущим enum `InterviewType`; переименовать enum сценария в `InterviewFormat` или назвать ORM-модель `InterviewTypeModel`.
- Добавить банк вопросов.
- Добавить источники вопросов.
- Добавить jobs генерации вопросов.
- Добавить связь сообщения/сессии с вопросом.
- Подготовить Alembic-миграцию.
- Обновить `schema_sync.py` для локального SQLite, если проект продолжает использовать auto-create/auto-sync.

### Новые сущности

#### InterviewType

- `id`;
- `title`;
- `role`;
- `technology_stack`;
- `description`;
- `levels`;
- `is_active`;
- `created_at`;
- `updated_at`.

#### Question

- `id`;
- `interview_type_id`;
- `level`;
- `question_text`;
- `expected_answer`;
- `evaluation_criteria`;
- `tags`;
- `source_id`;
- `is_active`;
- `created_at`;
- `updated_at`.

#### QuestionSource

- `id`;
- `title`;
- `url`;
- `source_type`;
- `retrieved_at`;
- `created_at`.

#### QuestionGenerationJob

- `id`;
- `interview_type_id`;
- `level`;
- `status`;
- `requested_count`;
- `generated_count`;
- `input_tokens`;
- `output_tokens`;
- `error_message`;
- `created_at`;
- `finished_at`.

#### SessionQuestion или поля в InterviewSession

Минимальный вариант:

- `InterviewSession.current_question_id`;
- `InterviewSession.question_index`;
- `Message.question_id`.

Более чистый вариант:

- отдельная таблица `session_questions`, если нужно хранить несколько вопросов и оценку по каждому.

На первом этапе достаточно минимального варианта, если он закрывает демонстрационный сценарий.

### Файлы

- `backend/app/models/interview.py`;
- `backend/app/db/base.py`;
- `backend/app/db/schema_sync.py`;
- новая миграция в `backend/alembic/versions`;
- `backend/tests/test_stage02_models.py`;
- `backend/tests/test_stage09_schema_sync.py`.

### Проверка

- `python -m unittest backend.tests.test_stage02_models`.
- `python -m unittest backend.tests.test_stage09_schema_sync`.
- `python -m unittest discover -s tests`.

### Критерий готовности

Модели банка вопросов существуют, таблицы создаются, тесты видят новые поля и связи.

## Этап 4. Admin API

### Работы

- Добавить dependency `get_current_admin_user`.
- Запретить обычному пользователю доступ к admin endpoints.
- Реализовать CRUD типов собеседований.
- Реализовать CRUD вопросов.
- Реализовать disable/enable вопроса.
- Реализовать запуск генерации вопросов.
- Реализовать просмотр jobs генерации.
- Реализовать ручное создание вопроса администратором.

### API

#### Interview types

- `GET /api/v1/admin/interview-types`;
- `POST /api/v1/admin/interview-types`;
- `PATCH /api/v1/admin/interview-types/{id}`;

#### Questions

- `GET /api/v1/admin/questions`;
- `POST /api/v1/admin/questions`;
- `PATCH /api/v1/admin/questions/{id}`;
- `PATCH /api/v1/admin/questions/{id}/disable`;
- `PATCH /api/v1/admin/questions/{id}/enable`.

#### Generation jobs

- `POST /api/v1/admin/interview-types/{id}/generate-questions`;
- `GET /api/v1/admin/question-generation-jobs`;

### Файлы

- `backend/app/api/deps.py`;
- `backend/app/api/endpoints/admin.py`;
- `backend/app/schemas/interview.py` или новые schemas:
  - `backend/app/schemas/interview_type.py`;
  - `backend/app/schemas/question.py`;
- `backend/app/services/question_generation.py`.

### Проверка

- Тест: администратор создаёт `InterviewType`.
- Тест: обычный пользователь получает `403` на admin endpoints.
- Тест: администратор создаёт/редактирует/отключает вопрос.
- Тест: список jobs возвращается только администратору.
- `python -m unittest discover -s tests`.

### Критерий готовности

Администратор может управлять основными справочниками через API, пользователь не может.

## Этап 5. Публичный API типов интервью

### Работы

- Добавить пользовательский endpoint для получения активных типов собеседований.
- Возвращать только активные `InterviewType`.
- Уровни должны приходить из БД.
- Если у типа нет активных вопросов по уровню, это должно быть понятно frontend.

### API

- `GET /api/v1/interview-types`;
- возможно `GET /api/v1/interview-types/{id}`.

### Файлы

- новый `backend/app/api/endpoints/interview_types.py`;
- `backend/app/api/api.py`;
- schemas для read DTO.

### Проверка

- Тест: пользователь видит активные типы.
- Тест: неактивные типы не отображаются в пользовательском API.
- Тест: endpoint доступен авторизованному пользователю.
- `python -m unittest discover -s tests`.

### Критерий готовности

Frontend больше не должен использовать захардкоженный список специализаций.

## Этап 6. Генерация банка вопросов

### Работы

- Реализовать `QuestionGenerationService`.
- Создавать `QuestionGenerationJob`.
- Формировать prompt для LLM с требованием вернуть JSON.
- Валидировать JSON через Pydantic.
- Сохранять `QuestionSource`.
- Сохранять `Question`.
- Обновлять статус job:
  - `pending`;
  - `running`;
  - `completed`;
  - `failed`.
- В mock-режиме генерировать реалистичные seed-like вопросы без внешнего API.
- В YandexGPT-режиме использовать единый LLM client.

### Формат LLM JSON

```json
[
  {
    "question_text": "Чем отличается ArrayList от LinkedList в Java?",
    "level": "junior",
    "tags": ["Java", "Collections", "Data Structures"],
    "expected_answer": "Кандидат должен объяснить различия в хранении данных, сложности доступа, вставки и удаления элементов.",
    "evaluation_criteria": [
      "понимание различий между массивом и связным списком",
      "знание сложности операций",
      "понимание практических сценариев применения"
    ],
    "source_title": "Java interview questions",
    "source_url": "https://example.com"
  }
]
```

### Файлы

- `backend/app/services/question_generation.py`;
- `backend/app/services/llm_client.py`;
- `backend/app/services/prompt_builder.py`;
- `backend/app/api/endpoints/admin.py`;
- tests для generation service.

### Проверка

- Тест: mock generation создаёт job и вопросы.
- Тест: некорректный JSON переводит job в `failed`.
- Тест: generated_count равен числу сохранённых вопросов.
- `python -m unittest discover -s tests`.

### Критерий готовности

На защите можно нажать "Сгенерировать вопросы" и показать сохранённый банк вопросов.

## Этап 7. Новый сценарий проведения интервью

### Работы

- Изменить создание `InterviewSession`:
  - принимать `interview_type_id`;
  - принимать `level`;
  - проверять наличие активных вопросов.
- При создании сессии выбрать первый активный вопрос из банка.
- Первое сообщение AI должно задавать конкретный вопрос из БД.
- При ответе пользователя сохранять `question_id`.
- LLM должен получать:
  - `question_text`;
  - `expected_answer`;
  - `evaluation_criteria`;
  - историю;
  - уровень;
  - роль/стек;
  - инструкции интервьюера.
- Если ответ неполный, LLM может задать уточняющий вопрос.
- После завершения формировать `InterviewResult`.

### Решение по этапам

Старую stage-flow модель можно упростить:

- `intro`;
- `question`;
- `follow_up`;
- `feedback`;
- `finished`.

Либо оставить текущие stages, но технический блок должен работать от банка вопросов. Для чистоты лучше сократить до сценария, который реально соответствует ВКР.

### Файлы

- `backend/app/services/interview_engine.py`;
- `backend/app/api/endpoints/interviews.py`;
- `backend/app/schemas/interview.py`;
- `backend/app/models/interview.py`;
- `backend/tests/test_stage04_interview_engine.py`;
- `backend/tests/test_stage10_endpoint_contracts.py`.

### Проверка

- Тест: нельзя создать интервью без активных вопросов.
- Тест: создание сессии выбирает вопрос из банка.
- Тест: первое AI-сообщение содержит вопрос из `Question`.
- Тест: пользовательское сообщение сохраняется с `question_id`.
- Тест: finish создаёт результат.
- `python -m unittest discover -s tests`.

### Критерий готовности

AI-интервьюер больше не придумывает вопрос с нуля в момент интервью.

## Этап 8. Структурированный результат и прогресс

### Работы

- Расширить `InterviewResult`, если нужно:
  - `strengths`;
  - `weaknesses`;
  - `recommendations`;
  - `summary`;
  - возможно `per_question_scores`.
- Сохранять сильные стороны, слабые места и рекомендации структурированно.
- Обновить `/progress`:
  - считать завершённые интервью;
  - средний балл;
  - динамику;
  - слабые критерии.
- Убрать из progress всё, что выглядит как тариф.
- Технические лимиты можно оставить в отдельном блоке или скрыть из UI.

### Файлы

- `backend/app/models/interview.py`;
- `backend/app/schemas/interview.py`;
- `backend/app/api/endpoints/progress.py`;
- `backend/app/services/interview_engine.py`;
- tests для progress/result.

### Проверка

- Тест: результат содержит score, strengths, weaknesses, recommendations.
- Тест: progress считается по завершённым интервью.
- Тест: progress не содержит коммерческих тарифных полей.
- `python -m unittest discover -s tests`.

### Критерий готовности

Результат выглядит как итог mock-собеседования, а не как общий текстовый отзыв.

## Этап 9. Seed-данные для защиты

### Работы

- Обновить seed так, чтобы он создавал:
  - администратора;
  - пользователя;
  - типы собеседований;
  - вопросы по уровням;
  - демонстрационную историю интервью;
  - демонстрационный результат.
- Seed должен быть идемпотентным.
- Удалить старые demo-данные, которые завязаны на legacy chat или старые enum-сценарии.

### Данные

#### Администратор

- email: `admin@example.com`;
- password: `admin123`.

#### Пользователь

- email: `user@example.com`;
- password: `user123`.

#### Типы собеседований

- Backend Java-разработчик;
- Frontend React-разработчик.

#### Уровни

- Junior;
- Middle;
- Senior.

### Файлы

- `backend/app/services/demo_seed.py`;
- `backend/scripts/seed_demo.py`;
- tests для seed.

### Проверка

- `python backend/scripts/seed_demo.py`.
- Тест: seed можно запустить дважды без дублей.
- Тест: есть admin/user.
- Тест: есть типы интервью и вопросы.
- `python -m unittest discover -s tests`.

### Критерий готовности

Проект можно быстро заполнить данными и показать на защите без ручной подготовки.

## Этап 10. Admin UI

### Работы

- Добавить admin routes.
- Показывать admin-навигацию только пользователю с `is_superuser=true` или `role=admin`.
- Реализовать страницу типов собеседований.
- Реализовать форму создания/редактирования типа.
- Реализовать страницу банка вопросов.
- Реализовать фильтры:
  - тип собеседования;
  - уровень;
  - тег;
  - активность.
- Реализовать редактирование вопроса, эталонного ответа и критериев.
- Реализовать включение/отключение вопроса.
- Реализовать запуск генерации вопросов и просмотр статуса job.

### Страницы

- `/admin/interview-types`;
- `/admin/questions`;
- `/admin/question-generation-jobs`.

### Файлы

- `frontend/src/App.tsx`;
- `frontend/src/components/Header.tsx`;
- `frontend/src/components/Sidebar.tsx`;
- `frontend/src/api/admin.ts`;
- `frontend/src/types/admin.ts`;
- `frontend/src/pages/admin/AdminInterviewTypes.tsx`;
- `frontend/src/pages/admin/AdminQuestions.tsx`;
- `frontend/src/pages/admin/AdminGenerationJobs.tsx`.

### Проверка

- `npm run build`.
- Frontend e2e: admin login -> список типов -> создать тип -> сгенерировать вопросы -> увидеть вопросы.
- Проверить, что обычный пользователь не видит admin-навигацию.

### Критерий готовности

Администратор может подготовить банк вопросов без прямого доступа к БД.

## Этап 11. Пользовательский frontend flow

### Работы

- Dashboard должен загружать `GET /interview-types`.
- В форме запуска интервью:
  - выбрать тип собеседования;
  - выбрать уровень из уровней этого типа;
  - показать стек и описание;
  - показать сообщение, если нет активных вопросов.
- Создание интервью должно отправлять `interview_type_id` и `level`.
- ChatPage должен показывать вопрос из банка.
- Result page должен показывать:
  - score;
  - сильные стороны;
  - слабые места;
  - рекомендации;
  - параметры интервью.
- ProfilePage должен показывать историю и прогресс без тарифных блоков.

### Файлы

- `frontend/src/pages/Dashboard.tsx`;
- `frontend/src/pages/ChatPage.tsx`;
- `frontend/src/pages/InterviewResult.tsx`;
- `frontend/src/pages/ProfilePage.tsx`;
- `frontend/src/api/interviews.ts`;
- `frontend/src/api/interviewTypes.ts`;
- `frontend/src/types/interview.ts`.

### Проверка

- `npm run build`.
- E2E: user login -> выбрать Backend Java -> Junior -> пройти короткое интервью -> finish -> result -> profile/history.

### Критерий готовности

Пользовательский сценарий полностью соответствует ВКР: выбор типа из БД, вопросы из банка, результат сохранён.

## Этап 12. Удаление коммерческой логики и финальная терминология

### Работы

- Финально проверить отсутствие:
  - tariff;
  - subscription;
  - pricing;
  - payment;
  - billing;
  - Free/Pro/Premium;
  - "тариф";
  - "подписка";
  - "оплата";
  - "премиум".
- Оставить только технические лимиты, если они нужны для защиты от расходов.
- В UI не показывать лимиты как пользовательский план.
- В README явно написать: коммерческой модели нет.

### Файлы

- весь backend;
- весь frontend;
- README;
- docs;
- tests.

### Проверка

- `rg -n -i --glob "!work-logs.md" --glob "!frontend/dist/**" "tariff|subscription|pricing|payment|billing|premium|free plan|Тариф|тариф|подписка|оплата|премиум|Free|Pro|Premium" .`
- `python -m unittest discover -s tests`.
- `npm run build`.

### Критерий готовности

В исходниках, UI и документации нет коммерческой модели.

## Этап 13. README и документация для защиты

### Работы

- Переписать README в нормальной UTF-8 кириллице.
- Описать:
  - назначение проекта;
  - стек;
  - backend запуск;
  - frontend запуск;
  - миграции;
  - seed;
  - env;
  - mock LLM;
  - YandexGPT;
  - тестовые логины;
  - сценарий демонстрации.
- Обновить `architecture.md`, если он остаётся в проекте.
- Убрать устаревшие инструкции про legacy chats.

### Файлы

- `README.md`;
- `architecture.md`;
- `.env.example`;
- возможно `instruction.md`.

### Проверка

- Пройти README вручную как checklist.
- Проверить, что команды запуска и тестов актуальны.
- Проверить, что test accounts соответствуют seed.

### Критерий готовности

По README можно поднять проект и повторить демонстрацию на защите.

## Этап 14. Полная проверка качества

### Работы

- Запустить backend-тесты.
- Запустить frontend build.
- Запустить e2e-сценарий, если окружение позволяет.
- Проверить OpenAPI в Swagger.
- Проверить seed на чистой SQLite-базе.
- Проверить роли:
  - admin видит admin UI;
  - user не имеет доступа к admin API/UI.
- Проверить отсутствие legacy chat.
- Проверить отсутствие коммерческой терминологии.

### Проверка

- `python -m unittest discover -s tests`.
- `npm run build`.
- `npm run test:e2e`.
- `rg -n "chats|Chat|chat_repo|/chats" backend frontend`.
- `rg -n -i --glob "!work-logs.md" --glob "!frontend/dist/**" "tariff|subscription|pricing|payment|billing|premium|Тариф|тариф|подписка|оплата|премиум|Free|Pro|Premium" .`

### Критерий готовности

Проект можно показывать как завершённый ВКР-продукт.

## Этап 15. Финальный демонстрационный сценарий

### Сценарий администратора

1. Войти как `admin@example.com`.
2. Открыть admin-раздел.
3. Создать тип собеседования "Backend Java-разработчик".
4. Указать роль, стек, описание и уровни Junior/Middle/Senior.
5. Запустить генерацию вопросов.
6. Открыть банк вопросов.
7. Показать вопрос, эталонный ответ и критерии оценки.
8. Отредактировать вопрос или отключить его.
9. Открыть статус generation job.

### Сценарий пользователя

1. Войти как `user@example.com`.
2. Открыть dashboard.
3. Выбрать "Backend Java-разработчик".
4. Выбрать уровень Junior или Middle.
5. Начать интервью.
6. Ответить на вопрос AI-интервьюера.
7. Получить уточняющий вопрос.
8. Завершить интервью.
9. Посмотреть оценку, сильные стороны, слабые места и рекомендации.
10. Открыть историю и прогресс.

### Проверка

- Пройти сценарий вручную.
- Если нужно для отчёта, обновить screenshots через конечный orchestration-скрипт.
- Проверить, что скриншоты не содержат legacy-чата, тарифов и пустых состояний.

### Критерий готовности

На защите очевидно, что IMock - это система mock-собеседований с банком вопросов, admin workflow, AI-оценкой и сохранением истории.

## Очередность реализации

Рекомендуемый порядок:

1. Этап 0: базовая фиксация состояния.
2. Этап 1: удалить legacy chat.
3. Этап 2: очистить LLM-слой.
4. Этап 3: добавить модели БД.
5. Этап 4: admin API.
6. Этап 5: публичный API типов интервью.
7. Этап 6: генерация вопросов.
8. Этап 7: новый interview engine.
9. Этап 8: результат и прогресс.
10. Этап 9: seed-данные.
11. Этап 10: admin UI.
12. Этап 11: user flow.
13. Этап 12: финальная очистка коммерческой терминологии.
14. Этап 13: README и документация.
15. Этап 14: полная проверка качества.
16. Этап 15: ручной демонстрационный сценарий.

## Definition of Done

Проект считается готовым, когда:

- legacy `/chats` полностью удалён;
- нет дублирующих LLM-сервисов;
- есть `InterviewType`, `Question`, `QuestionSource`, `QuestionGenerationJob`;
- вопросы берутся из БД;
- admin может создавать типы и вопросы;
- admin может запускать генерацию вопросов;
- пользователь проходит интервью по вопросам из банка;
- результат сохраняется и отображается;
- история и прогресс работают;
- seed создаёт admin/user и демонстрационные данные;
- backend-тесты проходят;
- frontend собирается;
- e2e-сценарий проходит или блокер окружения явно описан;
- README позволяет запустить проект;
- коммерческой логики нет.

## Дополнительный этап. Визуальная полировка интерфейса

### Статус

Выполнено.

### Что сделано

- Смягчена геометрия крупных карточек на странице результата интервью: уменьшены чрезмерные радиусы, добавлены устойчивые внутренние отступы.
- Иконки в заголовках карточек результата помещены в фиксированные компактные контейнеры, чтобы они не соприкасались с дугой скругления.
- Карточка "Фокус недели" в сайдбаре получила более аккуратную структуру: отдельный ряд для иконки и заголовка, увеличенный line-height и безопасные отступы.
- В чате уменьшена высота области сообщений, чтобы верхняя панель, чат и поле ввода помещались в демонстрационный viewport без заезда под sticky-header.
- Автоскролл сообщений в чате переведён на внутренний контейнер сообщений, чтобы не прокручивать всю страницу.
- CTA "Новое mock-собеседование" на dashboard сделан контрастным на тёмной hero-карточке.
- Обновлён Playwright-скрипт `screenshots:vkr`: он снова использует актуальные seed-данные, текущие маршруты и корректный запуск Vite на Windows.
- Пересобраны ВКР-скриншоты в `screenshots/vkr`.

### Изменённые файлы

- `frontend/src/pages/InterviewResult.tsx`;
- `frontend/src/components/Sidebar.tsx`;
- `frontend/src/pages/ChatPage.tsx`;
- `frontend/src/pages/Dashboard.tsx`;
- `frontend/tests/e2e/vkr-screenshots.mjs`;
- `screenshots/vkr/*.png`;
- `screenshots/vkr/README.md`.

### Проверка

- `npm run build` - успешно.
- `npm run screenshots:vkr` - успешно, скриншоты пересозданы через Playwright.
- Ручная визуальная проверка ключевых кадров: dashboard, настройка интервью, чат, результат.
- `npm run test:e2e` - успешно.

### Осталось

- Дальнейшие визуальные улучшения можно делать точечно после просмотра новых скриншотов в тексте ВКР, если при верстке отчёта потребуется другой кадр или масштаб.
