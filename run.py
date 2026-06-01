import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173

BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
API_URL = f"{BACKEND_URL}/api/v1"

IS_WINDOWS = os.name == "nt"
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


class ManagedProcess:
    def __init__(self, name: str, command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        print(f"[run] Запускаю {self.name}...")
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            creationflags=CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0,
        )

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self, timeout: int = 8) -> None:
        if not self.process or self.process.poll() is not None:
            return

        print(f"[run] Останавливаю {self.name}...")
        if IS_WINDOWS:
            try:
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
                self.process.wait(timeout=timeout)
                return
            except (subprocess.TimeoutExpired, OSError):
                pass

            subprocess.run(
                ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return

        self.process.send_signal(signal.SIGTERM)
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()


def backend_python() -> Path:
    executable = "python.exe" if IS_WINDOWS else "python"
    python_path = BACKEND_DIR / "venv" / ("Scripts" if IS_WINDOWS else "bin") / executable
    if not python_path.exists():
        raise FileNotFoundError(
            f"Не найден backend venv: {python_path}\n"
            "Создайте окружение и установите зависимости в папке backend."
        )
    return python_path


def run_checked(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Команда завершилась с ошибкой {result.returncode}: {' '.join(command)}")


def wait_for_url(url: str, name: str, timeout: int = 60) -> None:
    print(f"[run] Жду готовности {name}: {url}")
    started_at = time.monotonic()
    while time.monotonic() - started_at < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 500:
                    print(f"[run] {name} готов.")
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)

    raise TimeoutError(f"{name} не запустился за {timeout} секунд: {url}")


def frontend_command() -> list[str]:
    if IS_WINDOWS:
        return [
            "cmd.exe",
            "/c",
            "npm",
            "run",
            "dev",
            "--",
            "--host",
            FRONTEND_HOST,
            "--port",
            str(FRONTEND_PORT),
        ]
    return ["npm", "run", "dev", "--", "--host", FRONTEND_HOST, "--port", str(FRONTEND_PORT)]


def main() -> int:
    python_path = backend_python()
    processes: list[ManagedProcess] = []

    backend_env = os.environ.copy()
    backend_env["BACKEND_CORS_ORIGINS"] = ",".join(
        [
            f"http://localhost:{FRONTEND_PORT}",
            f"http://127.0.0.1:{FRONTEND_PORT}",
        ]
    )

    frontend_env = os.environ.copy()
    frontend_env["VITE_API_URL"] = API_URL

    try:
        print("[run] Подготавливаю demo-данные...")
        run_checked([str(python_path), "scripts/seed_demo.py"], BACKEND_DIR)

        backend = ManagedProcess(
            "backend",
            [
                str(python_path),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(BACKEND_PORT),
                "--reload",
            ],
            BACKEND_DIR,
            backend_env,
        )
        backend.start()
        processes.append(backend)
        wait_for_url(f"{API_URL}/admin/health", "backend")

        frontend = ManagedProcess("frontend", frontend_command(), FRONTEND_DIR, frontend_env)
        frontend.start()
        processes.append(frontend)
        wait_for_url(FRONTEND_URL, "frontend")

        print("")
        print("[run] Проект запущен.")
        print(f"[run] Frontend: {FRONTEND_URL}")
        print(f"[run] Backend API: {API_URL}")
        print("[run] Демо-вход: demo@imock.dev / demo12345")
        print("[run] Для остановки нажмите Ctrl+C.")

        while all(process.is_running() for process in processes):
            time.sleep(1)

        failed = [process.name for process in processes if process.process and process.process.poll() not in (None, 0)]
        if failed:
            print(f"[run] Один из процессов завершился с ошибкой: {', '.join(failed)}")
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n[run] Получен Ctrl+C.")
        return 0
    except Exception as exc:
        print(f"[run] Ошибка: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            process.stop()
        print("[run] Все процессы остановлены.")


if __name__ == "__main__":
    raise SystemExit(main())
