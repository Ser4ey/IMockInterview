import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { chromium } from 'playwright';

const frontendDir = process.cwd();
const rootDir = path.resolve(frontendDir, '..');
const backendDir = path.join(rootDir, 'backend');
const screenshotsDir = path.join(rootDir, 'screenshots', 'vkr');
const backendPort = 18120;
const frontendPort = 15192;
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}`;
const pythonExe = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
const viteEntry = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js');

const children = [];
const terminatingPids = new Set();

function normalizedEnv(extra = {}) {
  const env = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (key.toLowerCase() === 'path') {
      env.Path = value;
    } else if (!Object.keys(env).some((existingKey) => existingKey.toLowerCase() === key.toLowerCase())) {
      env[key] = value;
    }
  }
  return { ...env, ...extra };
}

function runChecked(command, args, options) {
  const result = spawnSync(command, args, { stdio: 'inherit', ...options });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}`);
  }
}

function startProcess(name, command, args, options) {
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: options.env,
    shell: false,
    stdio: 'ignore',
    windowsHide: true,
  });
  children.push(child);
  child.on('exit', (code) => {
    if (!terminatingPids.has(child.pid) && code !== null && code !== 0) {
      console.error(`${name} exited with code ${code}`);
    }
  });
  return child;
}

function killTree(pid) {
  if (!pid) return;
  terminatingPids.add(pid);
  if (process.platform === 'win32') {
    spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' });
    return;
  }
  try {
    process.kill(-pid, 'SIGTERM');
  } catch {
    try {
      process.kill(pid, 'SIGTERM');
    } catch {
      // Already stopped.
    }
  }
}

async function cleanup() {
  for (const child of children.reverse()) {
    killTree(child.pid);
  }
}

function canConnect(url) {
  return new Promise((resolve) => {
    const request = http.get(url, (response) => {
      response.resume();
      resolve(response.statusCode >= 200 && response.statusCode < 500);
    });
    request.on('error', () => resolve(false));
    request.setTimeout(1000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function waitForUrl(url, timeoutMs = 45_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await canConnect(url)) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function apiJson(pathname, token, options = {}) {
  const response = await fetch(`${backendUrl}/api/v1${pathname}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!response.ok) {
    throw new Error(`API ${pathname} failed with ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function loginDemoUser() {
  const params = new URLSearchParams();
  params.set('username', 'user@example.com');
  params.set('password', 'user123');
  const data = await apiJson('/auth/login/access-token', null, {
    method: 'POST',
    body: params,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data.access_token;
}

async function ensureDemoSessions(token) {
  const interviewTypes = await apiJson('/interview-types', token);
  const interviewType = interviewTypes.find((item) => item.title.includes('Backend Java')) ?? interviewTypes[0];
  if (!interviewType) {
    throw new Error('Не найден тип интервью для демонстрационных скриншотов.');
  }
  const level = interviewType.levels.includes('middle') ? 'middle' : interviewType.levels[0];

  let sessions = await apiJson('/interviews', token);
  let active = sessions.find((session) => session.status === 'active');
  let finished = sessions.find((session) => session.status === 'finished');

  if (!active) {
    active = await apiJson('/interviews', token, {
      method: 'POST',
      body: JSON.stringify({ interview_type_id: interviewType.id, level }),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (!finished) {
    const session = await apiJson('/interviews', token, {
      method: 'POST',
      body: JSON.stringify({ interview_type_id: interviewType.id, level }),
      headers: { 'Content-Type': 'application/json' },
    });
    await apiJson(`/interviews/${session.id}/messages`, token, {
      method: 'POST',
      body: JSON.stringify({
        content: 'Я бы начал с ресурсов предметной области, HTTP-методов, кодов статусов, валидации и контроля доступа.',
      }),
      headers: { 'Content-Type': 'application/json' },
    });
    const finishTurn = await apiJson(`/interviews/${session.id}/finish`, token, { method: 'POST' });
    finished = finishTurn.session;
  }

  return { active, finished };
}

async function gotoApp(page, pathname) {
  await page.goto(`${frontendUrl}${pathname}`, { waitUntil: 'domcontentloaded', timeout: 45_000 });
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
        caret-color: transparent !important;
      }
    `,
  }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 8_000 }).catch(() => {});
  await page.waitForTimeout(500);
}

async function waitVisible(locator, timeout = 15_000) {
  await locator.waitFor({ state: 'visible', timeout });
}

async function take(page, filename) {
  const outputPath = path.join(screenshotsDir, filename);
  await page.waitForTimeout(250);
  await page.screenshot({ path: outputPath, fullPage: false, animations: 'disabled' });
  console.log(`saved ${filename}`);
}

function writeReadme() {
  const readme = `# Скриншоты для ВКР IMock

Все изображения сделаны из локально запущенного веб-сервиса IMock через Playwright Chromium.

Viewport: 1440x1000.  
Формат: PNG.  
Демо-пользователь: user@example.com.

| Файл | Рисунок в отчёте | Назначение |
|---|---|---|
| fig_02_home_page.png | Рисунок 2 - Главная страница веб-сервиса IMock | Основная часть |
| fig_03_interview_setup.png | Рисунок 3 - Экран выбора параметров интервью | Основная часть |
| fig_04_interview_chat.png | Рисунок 4 - Интерфейс чата с ИИ-интервьюером | Основная часть |
| fig_05_interview_result.png | Рисунок 5 - Экран результата собеседования | Основная часть |
| fig_06_dashboard.png | Рисунок 6 - Личный кабинет пользователя | Основная часть |
| fig_B01_home_page.png | Рисунок Б - 1. Главная страница | Приложение Б |
| fig_B02_registration.png | Рисунок Б - 2. Страница регистрации | Приложение Б |
| fig_B03_interview_setup.png | Рисунок Б - 3. Страница выбора интервью | Приложение Б |
| fig_B04_interview_chat.png | Рисунок Б - 4. Чат интервью | Приложение Б |
| fig_B05_interview_result.png | Рисунок Б - 5. Экран результата | Приложение Б |
| fig_B06_dashboard.png | Рисунок Б - 6. Личный кабинет | Приложение Б |
`;
  fs.writeFileSync(path.join(screenshotsDir, 'README.md'), readme, 'utf8');
}

async function captureScreenshots() {
  const token = await loginDemoUser();
  const { active, finished } = await ensureDemoSessions(token);

  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      deviceScaleFactor: 1,
      locale: 'ru-RU',
      colorScheme: 'light',
    });

    const publicPage = await context.newPage();
    await gotoApp(publicPage, '/');
    await waitVisible(publicPage.getByRole('heading', { name: /Тренируйте собеседования/i }));
    await take(publicPage, 'fig_02_home_page.png');

    await publicPage.evaluate(() => window.scrollTo(0, 360));
    await take(publicPage, 'fig_B01_home_page.png');

    await gotoApp(publicPage, '/register');
    await waitVisible(publicPage.getByRole('heading', { name: 'Создайте пространство для подготовки' }));
    await publicPage.getByLabel('Имя').fill('Александр');
    await publicPage.getByLabel('Email').fill('alexander.demo@example.com');
    await publicPage.getByLabel('Пароль').fill('demo12345');
    await take(publicPage, 'fig_B02_registration.png');

    const authPage = await context.newPage();
    await gotoApp(authPage, '/');
    await authPage.evaluate((value) => localStorage.setItem('token', value), token);

    await gotoApp(authPage, '/dashboard');
    await waitVisible(authPage.getByRole('heading', { name: /выберите собеседование из банка IMock/i }));
    await take(authPage, 'fig_06_dashboard.png');

    await authPage.evaluate(() => window.scrollTo(0, 260));
    await take(authPage, 'fig_B06_dashboard.png');

    await authPage.evaluate(() => window.scrollTo(0, 0));
    await authPage.getByRole('button', { name: 'Новое mock-собеседование' }).click();
    await waitVisible(authPage.getByRole('heading', { name: 'Настройка интервью', exact: true }));
    await take(authPage, 'fig_03_interview_setup.png');
    await take(authPage, 'fig_B03_interview_setup.png');
    await authPage.keyboard.press('Escape');

    await gotoApp(authPage, `/interviews/${active.id}`);
    await waitVisible(authPage.getByRole('heading', { name: active.interview_type_title }));
    await waitVisible(authPage.getByPlaceholder('Введите ответ кандидата...'));
    await authPage.getByPlaceholder('Введите ответ кандидата...').fill('Я бы добавил cursor-based пагинацию, ограничение размера страницы и индексы под основные фильтры.');
    await take(authPage, 'fig_04_interview_chat.png');
    await take(authPage, 'fig_B04_interview_chat.png');

    await gotoApp(authPage, `/interviews/${finished.id}/result`);
    await waitVisible(authPage.getByRole('heading', { name: 'Разбор по критериям' }));
    await take(authPage, 'fig_05_interview_result.png');

    await authPage.evaluate(() => window.scrollTo(0, 0));
    await take(authPage, 'fig_B05_interview_result.png');

    writeReadme();
  } finally {
    await browser.close();
  }
}

async function main() {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  runChecked(pythonExe, ['scripts/seed_demo.py'], { cwd: backendDir });

  const env = normalizedEnv({
    VITE_API_URL: `${backendUrl}/api/v1`,
    BACKEND_CORS_ORIGINS: frontendUrl,
  });

  startProcess('backend-vkr', pythonExe, [
    '-m',
    'uvicorn',
    'app.main:app',
    '--host',
    '127.0.0.1',
    '--port',
    String(backendPort),
  ], { cwd: backendDir, env });

  startProcess('frontend-vkr', process.execPath, [
    viteEntry,
    '--host',
    '127.0.0.1',
    '--port',
    String(frontendPort),
  ], { cwd: frontendDir, env });

  try {
    await waitForUrl(`${backendUrl}/api/v1/admin/health`);
    await waitForUrl(frontendUrl);
    await captureScreenshots();
  } finally {
    await cleanup();
  }
}

main().catch(async (error) => {
  console.error(error);
  await cleanup();
  process.exit(1);
});
