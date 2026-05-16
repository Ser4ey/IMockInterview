# IMock

IMock - локальный сервис для проведения mock-собеседований. Текущая версия подготовлена для разработки и демонстрации ВКР без Docker: backend работает на FastAPI и SQLite, frontend - на React, Vite и Material UI.

## Что уже реализовано

- Регистрация и вход по JWT.
- Пользовательские интервью с типами `full`, `theory`, `self_presentation`, `technical`.
- Управляемый сценарий интервью по этапам: `intro`, `self_presentation`, `technical`, `practice`, `soft_skills`, `feedback`, `finished`.
- История сообщений и защита доступа: пользователь видит только свои интервью.
- Итоговый результат: общий балл, критерии, рекомендации.
- Локальный LLM-слой: `LLM_MODE=mock` по умолчанию и подготовленный провайдер `yandex`.
- Локальные дневные лимиты без Redis/Docker.
- Demo seed для быстрой демонстрации заполненной системы.
- Набор backend-тестов и обязательная TypeScript/Vite-сборка frontend.

## Локальный запуск без Docker

### Backend

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Backend будет доступен на `http://localhost:8000`.

Swagger: `http://localhost:8000/docs`.

При первом старте приложение создаёт таблицы SQLite автоматически через `Base.metadata.create_all`.

### Frontend

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend будет доступен на `http://localhost:5173`.

## Demo seed

Чтобы заполнить локальную базу демонстрационными данными:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python .\scripts\seed_demo.py
```

Демо-пользователь:

```text
email: demo@imock.dev
password: demo12345
```

Seed идемпотентный: его можно запускать повторно, он не должен плодить дубликаты.

## Настройка LLM

По умолчанию используется стабильный локальный режим:

```env
LLM_MODE=mock
```

Для будущей проверки YandexGPT:

```env
LLM_MODE=yandex
YANDEX_FOLDER_ID=...
YANDEX_API_KEY=...
```

Если `LLM_MODE=yandex`, но ключи не заданы, клиент безопасно откатывается к mock-режиму.

## Проверка

Backend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\backend
python -m unittest discover -s tests
```

Frontend:

```powershell
cd C:\Users\Sergey\Desktop\ВКР\IMock\frontend
npm run build
```

Эти две команды являются текущим обязательным минимумом перед защитной демонстрацией и перед дальнейшими доработками.

## Docker

Docker сейчас намеренно не является обязательным для локальной разработки. Его нужно возвращать отдельным 10-м этапом, когда локальный backend, frontend, тесты и демонстрационный сценарий уже стабильны.
