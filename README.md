# IMock

IMock - веб-сервис для проведения mock-собеседований на основе ИИ. Это не обычный чат: администратор создаёт типы собеседований и банк вопросов, а пользователь проходит интервью по заранее сохранённым вопросам, эталонным ответам и критериям оценки.

## Стек

- Backend: Python, FastAPI, async SQLAlchemy, SQLite, Alembic, JWT.
- Frontend: React, TypeScript, Vite, Material UI.
- LLM: `mock` для локальной демонстрации и `yandex_agents` для AI Studio Agents.

## LLM-режимы

В проекте поддерживаются только два режима:

```env
LLM_MODE=mock
```

Локальный режим без внешних запросов. Используется по умолчанию для тестов и демонстрации.

```env
LLM_MODE=yandex_agents
```

Production-режим через 3 текстовых агента Yandex AI Studio:

- `imock-question-bank-generator` - генерация банка вопросов, Web Search включён.
- `imock-interviewer` - ведение интервью по текущему вопросу, Web Search выключен.
- `imock-interview-reviewer` - итоговая оценка интервью, Web Search выключен.

Старый прямой completion-режим через одиночный YandexGPT endpoint удалён.

## Backend env

Создайте файл `backend/.env` на основе `backend/.env.example`:

```env
PROJECT_NAME=IMock
API_V1_STR=/api/v1
DATABASE_URL=sqlite+aiosqlite:///./imock.db
SECRET_KEY=change-me-in-local-env
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174

LLM_MODE=mock

YANDEX_FOLDER_ID=
YANDEX_API_KEY=
YANDEX_AI_STUDIO_BASE_URL=https://ai.api.cloud.yandex.net/v1
YANDEX_QUESTION_AGENT_MODEL=
YANDEX_INTERVIEW_AGENT_MODEL=
YANDEX_REVIEW_AGENT_MODEL=
YANDEX_AGENTS_TIMEOUT_SECONDS=60
YANDEX_AGENT_STORE_RESPONSES=false
```

Для режима `yandex_agents` заполните `YANDEX_API_KEY`, `YANDEX_FOLDER_ID` и три значения `YANDEX_*_AGENT_MODEL`. Значения agent model берите из AI Studio в блоке "Посмотреть код", из поля `model`.

API-ключи нельзя коммитить в репозиторий.

## Настройка агентов AI Studio

### Question Bank Generator

- Model: YandexGPT 5.1 Pro.
- Tools: Web Search включён.
- Temperature: `0.25`.
- Max output tokens: `4000`.
- Response format: strict JSON schema.
- Ответ: объект `{ "questions": [...] }`.

### Interviewer

- Model: YandexGPT 5.1 Pro.
- Tools: выключены.
- Temperature: `0.35`.
- Max output tokens: `900`.
- Response format: strict JSON schema.
- Ответ: `message`, `should_ask_follow_up`, `covered_criteria`, `missing_criteria`.

### Interview Reviewer

- Model: YandexGPT 5.1 Pro.
- Tools: выключены.
- Temperature: `0.2`.
- Max output tokens: `1800`.
- Response format: strict JSON schema.
- Ответ: `score`, `correctness`, `completeness`, `depth`, `communication`, `strengths`, `weaknesses`, `recommendations`, `summary`.

## Запуск

Backend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Seed:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python .\scripts\seed_demo.py
```

Тестовые пользователи:

- admin: `admin@example.com` / `admin123`
- user: `user@example.com` / `user123`

## Проверки

Backend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python -m unittest discover -s tests
```

Frontend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\frontend
npm run build
npm run test:e2e
npm run screenshots:vkr
```

Live smoke для AI Studio Agents:

1. Создать 3 агента в AI Studio.
2. Заполнить `backend/.env`.
3. Установить `LLM_MODE=yandex_agents`.
4. Перезапустить backend.
5. Войти как admin и сгенерировать 1 вопрос.
6. Войти как user, пройти короткое интервью, завершить его и проверить результат.

## Основной сценарий защиты

1. Войти как администратор.
2. Создать тип собеседования.
3. Запустить генерацию вопросов.
4. Показать банк вопросов, эталонные ответы, критерии и источники.
5. Войти как пользователь.
6. Выбрать тип собеседования и уровень.
7. Пройти интервью.
8. Получить итоговую оценку.
9. Открыть историю и прогресс.

## Важно

В проекте нет тарифов, подписок, оплат, Free/Pro/Premium и коммерческих ограничений. Технические лимиты используются только как защита от неконтролируемого расходования LLM API.
