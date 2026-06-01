# Инструкция по запуску и настройке проекта IMock

## О проекте
**IMock** — это сервис для проведения mock-собеседований с использованием ИИ (YandexGPT).
Проект состоит из двух частей:
- **Backend**: FastAPI (Python), SQLite, SQLAlchemy, Alembic.
- **Frontend**: React (Vite), Material UI.

## Предварительные требования
- Python 3.10+
- Node.js 18+
- Git

## 1. Настройка окружения (Backend)

1. Перейдите в папку backend:
   ```bash
   cd backend
   ```

2. Создайте виртуальное окружение и активируйте его:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в папке `backend` (если его нет) и заполните его:
   ```env
   # Security
   SECRET_KEY="supersecretkey_change_me"
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   
   # Database
   DATABASE_URL="sqlite+aiosqlite:///./imock.db"
   
   # CORS (список разрешенных источников)
   BACKEND_CORS_ORIGINS='["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]'
   
   # Yandex Cloud (для работы ИИ)
   YANDEX_FOLDER_ID="ваш_folder_id_из_яндекс_облака"
   YANDEX_API_KEY="ваш_api_key_или_iam_token"
   ```
   > **Важно:** Без `YANDEX_FOLDER_ID` и `YANDEX_API_KEY` функции собеседования работать не будут (будут ошибки при генерации вопросов).

5. Примените миграции базы данных:
   ```bash
   alembic upgrade head
   ```

## 2. Запуск Backend

В папке `backend` выполните команду:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Сервер запустится на `http://localhost:8000`.
Документация API доступна по адресу: `http://localhost:8000/docs`.

## 3. Запуск Frontend

1. Перейдите в папку frontend:
   ```bash
   cd ../frontend
   ```

2. Установите зависимости:
   ```bash
   npm install
   ```

3. Запустите сервер разработки:
   ```bash
   npm run dev
   ```
   Сайт откроется по адресу `http://localhost:5173` (или 5174, если порт занят).

## Основной функционал

1. **Регистрация/Вход**: Создайте аккаунт (/register).
2. **Дашборд**: Просмотр списка своих собеседований.
3. **Новое собеседование**: Нажмите "Начать собеседование", выберите позицию (Backend, Frontend и т.д.) и уровень (Junior, Middle).
4. **Чат с ИИ**: Отвечайте на вопросы ИИ. Интервьюер будет задавать вопросы последовательно.
5. **Завершение**: Нажмите "Завершить", чтобы получить отзыв (Feedback) и оценку от ИИ.

## Частые проблемы

- **Ошибка CORS**: Убедитесь, что адрес фронтенда (например, `http://localhost:5173`) добавлен в `BACKEND_CORS_ORIGINS` в `.env`.
- **Ошибка 404/405 при регистрации**: Проверьте, что бэкенд запущен и доступен по адресу `http://localhost:8000`.
- **Alembic error**: Если возникают ошибки миграций, попробуйте удалить файл `imock.db` и папку `backend/alembic/versions` (кроме `env.py`), и заново инициализировать миграции (только для разработки!).
