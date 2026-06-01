# AGENTS.md

## Проект

IMock - веб-сервис для проведения mock-собеседований с AI-интервьюером. Главная цель текущей разработки - подготовить рабочий продукт и качественные материалы для отчета ВКР.

## Дизайн

Перед любыми изменениями frontend-интерфейса обязательно сверяйся со спецификацией:

- [docs/design-nordic-studio.md](docs/design-nordic-studio.md)

Основной визуальный стиль проекта - **Nordic Studio**: теплый современный минимализм, темно-зеленый акцент, мягкие карточки, русскоязычный интерфейс, без ощущения дефолтного Material UI-шаблона.

## Требования к frontend

- Пользовательский интерфейс должен быть на русском языке.
- Ошибки должны отображаться в интерфейсе, а не приводить к белому экрану.
- Для демонстрационных сценариев ВКР допускаются seed/mock-данные, если реальный LLM недоступен.
- Скриншоты для отчета должны сниматься только с работающего приложения, без devtools, пустых состояний и технического мусора.

## Проверки

После изменений в frontend минимум запускай:

- `npm run build` из папки `frontend`.

Если меняется пользовательский сценарий, дополнительно запускай e2e-тесты Playwright:

- `npm run test:e2e` из папки `frontend`.
## Command Rules

These rules are mandatory for future Codex sessions in this project. They exist because several local commands on Windows either block the agent process indefinitely or fail repeatedly due to environment/path issues.

### Required pre-command checklist

Before running any shell command, the agent must check this section and `work-logs.md`.

For every shell command, write a new entry to `work-logs.md` before execution with:

- the exact command;
- whether it is expected to finish or start a background process;
- why it should not block;
- the timeout;
- the expected result.

If a command resembles any forbidden pattern below, do not run it. Choose a safer finite script or ask the user before proceeding.

### Forbidden blocking commands

Do not run these commands directly through `shell_command`, because they can start long-running processes and block the chat:

- `npm run dev`
- `npm run dev -- ...`
- `vite`
- `.\node_modules\.bin\vite.cmd ...`
- `python -m uvicorn ...`
- `.\venv\Scripts\python.exe -m uvicorn ...`
- `uvicorn app.main:app ...`
- `cmd.exe /c start "..." /B ...`
- any foreground backend/frontend server command;
- any command that starts a watcher, server, or REPL and does not have a guaranteed finite exit.

The command below is explicitly known to block in this environment and must not be used:

```powershell
cmd.exe /c start "IMock Backend" /B ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 18110
```

### Safe server orchestration rule

If backend and frontend must be started for verification or screenshots, use a finite orchestration script instead of direct server commands.

The script must:

- start backend and frontend with controlled subprocesses;
- redirect stdout/stderr to log files;
- wait for readiness with fixed timeouts;
- run tests or Playwright screenshots;
- stop all spawned child processes in `finally`;
- exit on its own.

Do not rely on shell-level backgrounding such as `start /B` as a safety mechanism.

### Known Windows and environment pitfalls

The project path contains Cyrillic characters: `C:\Users\Sergey\Desktop\ВКР\IMock`.

Repeated failures caused by this environment:

- Some Node/Playwright/Vite child processes show mojibake paths such as `Р’РљР ` instead of `ВКР`.
- Vite can fail with `spawn EPERM` while starting `esbuild` inside the sandbox.
- Playwright/Chromium can fail with `spawn EPERM` inside the sandbox.
- `Start-Process` can fail with `Item has already been added. Key in dictionary: 'PATH' Key being added: 'Path'`.
- PowerShell virtualenv launchers can break if the venv was created from a path without Cyrillic and later moved into a Cyrillic path.

How to avoid these issues:

- Prefer existing project virtualenv paths only after validating them with a finite command.
- Do not repeatedly retry the same failing command with minor argument changes.
- If `spawn EPERM` appears for browser/Vite/esbuild, treat it as a sandbox/environment blocker and use an approved finite script outside the sandbox rather than foreground commands.
- For screenshots, prefer a single finite Node/Python orchestration script that starts servers, runs Playwright, and cleans up.
- If path encoding causes repeated failures, move/copy only the execution workspace to an ASCII temp path such as `C:\tmp\imock-run` for runtime verification, while keeping source edits in the real project folder.

### Current screenshot workflow status

Known facts from the latest run:

- Backend API login works at `http://127.0.0.1:18110/api/v1/auth/login/access-token`.
- `/api/v1/auth/me` works through direct HTTP requests.
- Frontend can serve public pages on `http://127.0.0.1:15190`.
- Playwright successfully created the first three screenshots before failing:
  - `fig_02_home_page.png`
  - `fig_B01_home_page.png`
  - `fig_B02_registration.png`
- Authenticated pages failed because the browser request to `/api/v1/auth/me` was blocked by CORS for origin `http://127.0.0.1:15190`.
- `backend/app/core/config.py` was patched to include `http://localhost:15190` and `http://127.0.0.1:15190`, but backend was not successfully restarted after the patch because the restart command blocked.

Next safe path:

- Do not manually start backend/frontend with shell server commands.
- Create or use a finite orchestration script that launches both services, waits for readiness, runs screenshot capture, and kills child processes.
- Alternatively, run frontend on an already allowed origin such as `http://127.0.0.1:5173` to avoid needing backend restart for CORS.
