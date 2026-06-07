import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const frontendDir = path.join(repoRoot, 'frontend');
const screenshotsDir = path.join(repoRoot, 'screenshots', 'vkr');
const logsDir = path.join(screenshotsDir, '.runtime');
const frontendHost = process.env.IMOCK_SCREENSHOT_HOST || '127.0.0.1';
const frontendPort = Number(process.env.IMOCK_SCREENSHOT_PORT || 15191);
const frontendUrl = `http://${frontendHost}:${frontendPort}`;
const stage = process.argv.find((arg) => arg.startsWith('--stage='))?.split('=')[1] || 'all';

const requireFromFrontend = createRequire(path.join(frontendDir, 'package.json'));
const { chromium } = requireFromFrontend('playwright');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const demoUser = {
  id: 1,
  email: 'demo@imock.dev',
  full_name: 'Александр Петров',
  role: 'user',
  is_active: true,
  is_superuser: false,
  requests_count: 8,
  created_at: '2026-05-12T09:00:00',
};

const demoInterviewTypes = [
  {
    id: 1,
    title: 'Backend Java-разработчик',
    role: 'Backend Java-разработчик',
    technology_stack: 'Java, Spring Boot, PostgreSQL, REST API',
    description: 'Техническое собеседование по backend-разработке и проектированию API.',
    levels: ['middle', 'senior'],
    is_active: true,
    created_at: '2026-05-01T09:00:00',
    updated_at: null,
    question_counts: { middle: 12, senior: 8 },
  },
  {
    id: 2,
    title: 'Frontend React-разработчик',
    role: 'Frontend React-разработчик',
    technology_stack: 'React, TypeScript, UI architecture',
    description: 'Собеседование по frontend-разработке, состоянию приложения и компонентному дизайну.',
    levels: ['junior', 'middle'],
    is_active: true,
    created_at: '2026-05-01T09:00:00',
    updated_at: null,
    question_counts: { junior: 10, middle: 9 },
  },
];

const activeSession = {
  id: 101,
  user_id: 1,
  interview_type_id: 1,
  interview_type_title: 'Backend Java-разработчик',
  role: 'Backend Java-разработчик',
  technology_stack: 'Java, Spring Boot, PostgreSQL, REST API',
  level: 'middle',
  status: 'active',
  stage: 'question',
  current_question_id: 1,
  question_index: 1,
  started_at: '2026-05-12T10:30:00',
  finished_at: null,
};

const resultSession = {
  id: 201,
  user_id: 1,
  interview_type_id: 1,
  interview_type_title: 'Backend Java-разработчик',
  role: 'Backend Java-разработчик',
  technology_stack: 'Java, Spring Boot, PostgreSQL, REST API',
  level: 'middle',
  status: 'finished',
  stage: 'finished',
  current_question_id: null,
  question_index: 4,
  started_at: '2026-05-11T11:00:00',
  finished_at: '2026-05-11T11:45:00',
};

const demoSessions = [
  activeSession,
  resultSession,
  {
    id: 202,
    user_id: 1,
    interview_type_id: 1,
    interview_type_title: 'Backend Java-разработчик',
    role: 'Backend Java-разработчик',
    technology_stack: 'Java, Spring Boot, PostgreSQL, REST API',
    level: 'middle',
    status: 'finished',
    stage: 'finished',
    current_question_id: null,
    question_index: 3,
    started_at: '2026-05-09T16:00:00',
    finished_at: '2026-05-09T16:35:00',
  },
  {
    id: 203,
    user_id: 1,
    interview_type_id: 2,
    interview_type_title: 'Frontend React-разработчик',
    role: 'Frontend React-разработчик',
    technology_stack: 'React, TypeScript, UI architecture',
    level: 'middle',
    status: 'finished',
    stage: 'finished',
    current_question_id: null,
    question_index: 5,
    started_at: '2026-05-07T14:00:00',
    finished_at: '2026-05-07T14:50:00',
  },
];

const demoMessages = [
  {
    id: 1,
    session_id: activeSession.id,
    sender: 'ai',
    content: 'Расскажите, пожалуйста, как устроена архитектура REST API и какие принципы вы соблюдаете при проектировании эндпоинтов?',
    created_at: '2026-05-12T10:31:00',
  },
  {
    id: 2,
    session_id: activeSession.id,
    sender: 'user',
    content: 'Я проектирую API с учётом принципов REST: использую ресурсы, HTTP-методы GET, POST, PUT, DELETE, коды статусов, валидацию входных данных и разграничение доступа.',
    created_at: '2026-05-12T10:34:00',
  },
  {
    id: 3,
    session_id: activeSession.id,
    sender: 'ai',
    content: 'Хорошо. А как бы вы спроектировали пагинацию для большого списка данных?',
    created_at: '2026-05-12T10:35:00',
  },
];

const demoResult = {
  id: 1,
  session_id: resultSession.id,
  score: 84,
  correctness: 86,
  completeness: 82,
  depth: 80,
  communication: 88,
  strengths: [
    'Уверенно объясняет REST-подход и назначение HTTP-методов.',
    'Связывает проектирование API с валидацией, доступом и кодами статусов.',
  ],
  weaknesses: [
    'Стоит подробнее проговаривать trade-off при выборе пагинации и кеширования.',
    'Ответы можно усиливать конкретными примерами из PostgreSQL и сервисного слоя.',
  ],
  recommendations:
    'Сильные стороны: уверенное понимание REST, HTTP-методов и базовой архитектуры API. Зоны роста: подробнее раскрывать trade-off при выборе пагинации, стратегий кеширования и изоляции бизнес-логики. Рекомендуется повторить транзакции, индексы PostgreSQL и паттерны проектирования сервисного слоя.',
  summary:
    'Кандидат показывает уверенную базу backend-разработки и способен структурировать ответы. Для более высокого результата нужно глубже раскрывать архитектурные компромиссы.',
  created_at: '2026-05-11T11:46:00',
};

async function waitForHttp(url, timeoutMs = 45_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1_500) });
      if (response.ok) return;
    } catch {
      await sleep(500);
    }
  }

  throw new Error(`Timed out waiting for ${url}`);
}

async function isHttpReady(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1_500) });
    return response.ok;
  } catch {
    return false;
  }
}

function startFrontend() {
  fs.mkdirSync(logsDir, { recursive: true });

  const viteBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js');
  if (!fs.existsSync(viteBin)) {
    throw new Error(`Vite binary was not found: ${viteBin}`);
  }

  const out = fs.openSync(path.join(logsDir, 'vite.out.log'), 'a');
  const err = fs.openSync(path.join(logsDir, 'vite.err.log'), 'a');
  const child = spawn(
    process.execPath,
    [viteBin, '--host', frontendHost, '--port', String(frontendPort), '--strictPort'],
    {
      cwd: frontendDir,
      env: {
        ...process.env,
        VITE_API_URL: process.env.VITE_API_URL || 'http://127.0.0.1:18110/api/v1',
      },
      detached: false,
      stdio: ['ignore', out, err],
      windowsHide: true,
    },
  );

  child.on('exit', (code, signal) => {
    fs.appendFileSync(path.join(logsDir, 'vite.out.log'), `\n[vkr-screenshots] vite exited code=${code} signal=${signal}\n`);
  });

  return child;
}

async function ensureFrontend() {
  if (await isHttpReady(frontendUrl)) {
    return null;
  }

  const child = startFrontend();
  try {
    await waitForHttp(frontendUrl);
    return child;
  } catch (error) {
    await stopProcess(child);
    throw error;
  }
}

async function stopProcess(child) {
  if (!child || child.killed) return;
  child.kill('SIGTERM');
  await sleep(800);
  if (!child.killed) child.kill('SIGKILL');
}

async function fulfillJson(route, body, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify(body),
  });
}

async function installDemoApi(context) {
  await context.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname.replace(/^\/api\/v1/, '');
    const method = request.method();

    if (method === 'GET' && pathname === '/auth/me') {
      return fulfillJson(route, demoUser);
    }

    if (method === 'GET' && pathname === '/interviews') {
      return fulfillJson(route, demoSessions);
    }

    if (method === 'GET' && pathname === '/interview-types') {
      return fulfillJson(route, demoInterviewTypes);
    }

    if (method === 'POST' && pathname === '/interviews') {
      return fulfillJson(route, activeSession, 201);
    }

    const sessionMatch = pathname.match(/^\/interviews\/(\d+)$/);
    if (method === 'GET' && sessionMatch) {
      const id = Number(sessionMatch[1]);
      const session = demoSessions.find((item) => item.id === id);
      return fulfillJson(route, session || activeSession);
    }

    if (method === 'GET' && pathname === `/interviews/${activeSession.id}/messages`) {
      return fulfillJson(route, demoMessages);
    }

    if (method === 'GET' && pathname === `/interviews/${resultSession.id}/result`) {
      return fulfillJson(route, demoResult);
    }

    if (method === 'POST' && pathname.endsWith('/messages')) {
      return fulfillJson(route, {
        session: activeSession,
        messages: [
          {
            id: 4,
            session_id: activeSession.id,
            sender: 'user',
            content: 'Я бы добавил cursor-based пагинацию и ограничение размера страницы.',
            created_at: '2026-05-12T10:37:00',
          },
        ],
        result: null,
      });
    }

    if (method === 'POST' && pathname.endsWith('/finish')) {
      return fulfillJson(route, {
        session: { ...activeSession, status: 'finished', stage: 'finished' },
        messages: [],
        result: demoResult,
      });
    }

    return fulfillJson(route, { detail: `Unhandled mock route: ${method} ${pathname}` }, 404);
  });
}

async function createBrowserPage({ authenticated = false, mockApi = false } = {}) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    locale: 'ru-RU',
    colorScheme: 'light',
  });

  if (mockApi) {
    await installDemoApi(context);
  }

  if (authenticated) {
    await context.addInitScript(() => {
      localStorage.setItem('token', 'demo-vkr-token');
    });
  }

  const page = await context.newPage();
  page.setDefaultTimeout(20_000);
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        scroll-behavior: auto !important;
      }
    `,
  }).catch(() => {});

  return { browser, page };
}

async function take(page, fileName) {
  await page.screenshot({
    path: path.join(screenshotsDir, fileName),
    fullPage: false,
    animations: 'disabled',
  });
  console.log(`saved ${fileName}`);
}

async function capturePublicPages() {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const { browser, page } = await createBrowserPage();
  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /Тренируйте собеседования/i }).waitFor();
    await take(page, 'fig_02_home_page.png');

    await page.evaluate(() => window.scrollTo(0, 360));
    await take(page, 'fig_B01_home_page.png');

    await page.goto(`${frontendUrl}/register`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /Создайте пространство для подготовки/i }).waitFor();
    await page.getByLabel('Имя').fill('Александр Петров');
    await page.getByLabel('Email').fill('alexander.demo@example.com');
    await page.getByLabel('Пароль').fill('demo12345');
    await take(page, 'fig_B02_registration.png');
  } finally {
    await browser.close();
  }
}

async function captureDashboardPages() {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const { browser, page } = await createBrowserPage({ authenticated: true, mockApi: true });
  try {
    await page.goto(`${frontendUrl}/dashboard`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }).waitFor();
    await take(page, 'fig_06_dashboard.png');

    await page.evaluate(() => window.scrollTo(0, 260));
    await take(page, 'fig_B06_dashboard.png');
  } finally {
    await browser.close();
  }
}

async function captureSetupPages() {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const { browser, page } = await createBrowserPage({ authenticated: true, mockApi: true });
  try {
    await page.goto(`${frontendUrl}/dashboard`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }).waitFor();
    await page.getByRole('button', { name: /Новое mock-собеседование/i }).click();
    await page.getByRole('dialog').waitFor();
    await page.getByRole('heading', { name: /Настройка интервью/i }).waitFor();
    await page.getByText(/Активных вопросов для уровня/i).waitFor();
    await take(page, 'fig_03_interview_setup.png');
    await take(page, 'fig_B03_interview_setup.png');
  } finally {
    await browser.close();
  }
}

async function captureInterviewPages() {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const { browser, page } = await createBrowserPage({ authenticated: true, mockApi: true });
  try {
    await page.goto(`${frontendUrl}/interviews/${activeSession.id}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: activeSession.interview_type_title }).waitFor();
    await page.getByText(/Расскажите, пожалуйста, как устроена архитектура REST API/i).waitFor();
    await page.getByPlaceholder(/Введите ответ кандидата/i).fill('Я бы добавил cursor-based пагинацию, ограничение размера страницы и стабильную сортировку по неизменяемому полю.');
    await take(page, 'fig_04_interview_chat.png');
    await take(page, 'fig_B04_interview_chat.png');

    await page.goto(`${frontendUrl}/interviews/${resultSession.id}/result`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: /Разбор по критериям/i }).waitFor();
    await take(page, 'fig_05_interview_result.png');

    await page.evaluate(() => window.scrollTo(0, 320));
    await take(page, 'fig_B05_interview_result.png');
  } finally {
    await browser.close();
  }
}

function writeReadme() {
  const readme = `# Скриншоты для ВКР IMock

Скриншоты сделаны из локально запущенного frontend-приложения IMock через Playwright Chromium.
Для авторизованных страниц используется стабильный demo API mock, чтобы изображения были воспроизводимыми и не зависели от LLM/API-ключей.

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
  console.log('saved README.md');
}

async function main() {
  if (!['home', 'public', 'dashboard', 'setup', 'interview', 'all'].includes(stage)) {
    throw new Error(`Stage "${stage}" is not implemented yet`);
  }

  const frontend = await ensureFrontend();
  try {
    if (stage === 'all') {
      await capturePublicPages();
      await captureDashboardPages();
      await captureSetupPages();
      await captureInterviewPages();
      writeReadme();
    } else if (stage === 'dashboard') {
      await captureDashboardPages();
    } else if (stage === 'setup') {
      await captureSetupPages();
    } else if (stage === 'interview') {
      await captureInterviewPages();
    } else {
      await capturePublicPages();
    }
  } finally {
    await stopProcess(frontend);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
