import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const backendDir = path.join(rootDir, 'backend');
const frontendDir = path.join(rootDir, 'frontend');
const backendPort = 18000;
const frontendPort = 15173;
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}`;
const demoAdminEmail = 'admin@example.com';
const demoAdminPassword = 'admin123';
function resolveBackendPython() {
  if (process.env.IMOCK_BACKEND_PYTHON) {
    return process.env.IMOCK_BACKEND_PYTHON;
  }
  const venvPython = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  throw new Error(
    `Backend Python executable not found at ${venvPython}. ` +
      'Create backend venv or set IMOCK_BACKEND_PYTHON to a Python executable with backend dependencies installed.',
  );
}

const pythonExe = resolveBackendPython();

const children = [];
const terminatingPids = new Set();
let currentPage = null;

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

function logPath(name) {
  return path.join(rootDir, `${name}.log`);
}

function runChecked(command, args, options) {
  const result = spawnSync(command, args, { stdio: 'inherit', ...options });
  if (result.error) {
    throw new Error(`${command} ${args.join(' ')} failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}`);
  }
}

function startProcess(name, command, args, options) {
  const out = fs.openSync(logPath(name), 'w');
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: options.env,
    shell: false,
    stdio: ['ignore', out, out],
    windowsHide: true,
  });
  children.push(child);
  child.on('exit', (code) => {
    if (!terminatingPids.has(child.pid) && code !== null && code !== 0) {
      console.error(`${name} exited with code ${code}. See ${logPath(name)}`);
    }
  });
  return child;
}

function killTree(pid) {
  if (!pid) return;
  terminatingPids.add(pid);
  if (process.platform === 'win32') {
    spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' });
  } else {
    try {
      process.kill(-pid, 'SIGTERM');
    } catch {
      process.kill(pid, 'SIGTERM');
    }
  }
}

async function cleanup() {
  for (const child of children.reverse()) {
    killTree(child.pid);
  }
}

async function waitForUrl(url, timeoutMs = 45_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await canConnect(url)) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function expectVisible(locator, timeout = 15_000) {
  await locator.waitFor({ state: 'visible', timeout });
}

async function gotoApp(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90_000 });
}

async function assertLayoutLooksStable(page) {
  const issues = await page.evaluate(() => {
    const result = [];
    if (document.body.scrollWidth > window.innerWidth + 1) {
      result.push(`horizontal overflow: body=${document.body.scrollWidth}, viewport=${window.innerWidth}`);
    }

    const surfaces = Array.from(document.querySelectorAll('.MuiPaper-root, .MuiAppBar-root'));
    const oversized = surfaces
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        const radius = Number.parseFloat(getComputedStyle(element).borderTopLeftRadius || '0');
        return radius > 28.5;
      })
      .slice(0, 5)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return `${element.className} radius=${getComputedStyle(element).borderTopLeftRadius} size=${Math.round(rect.width)}x${Math.round(rect.height)}`;
      });
    if (oversized.length) result.push(`oversized surface radius: ${oversized.join(' | ')}`);

    return result;
  });
  if (issues.length) {
    throw new Error(`Layout regression detected:\n${issues.join('\n')}`);
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

async function main() {
  process.on('exit', () => {
    for (const child of children.reverse()) killTree(child.pid);
  });

  runChecked(pythonExe, ['scripts/seed_demo.py'], { cwd: backendDir });

  startProcess('backend-e2e', pythonExe, [
    '-m',
    'uvicorn',
    'app.main:app',
    '--host',
    '127.0.0.1',
    '--port',
    String(backendPort),
  ], {
    cwd: backendDir,
    env: normalizedEnv({
      BACKEND_CORS_ORIGINS: frontendUrl,
      ADMIN_EMAIL: demoAdminEmail,
      ADMIN_PASSWORD: demoAdminPassword,
    }),
  });

  const frontendCommand = process.platform === 'win32' ? 'cmd.exe' : 'npm';
  const frontendArgs = process.platform === 'win32'
    ? ['/c', 'npm', 'run', 'dev', '--', '--host', '127.0.0.1', '--port', String(frontendPort)]
    : ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(frontendPort)];

  startProcess('frontend-e2e', frontendCommand, frontendArgs, {
    cwd: frontendDir,
    env: normalizedEnv({ VITE_API_URL: `${backendUrl}/api/v1` }),
  });

  await waitForUrl(`${backendUrl}/api/v1/admin/health`);
  await waitForUrl(frontendUrl);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  currentPage = page;
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrors.push(error.message));

  await gotoApp(page, `${frontendUrl}/register`);
  await expectVisible(page.getByRole('heading', { name: 'Создайте пространство для подготовки' }));
  await page.getByLabel('Имя').fill('Пользователь');
  await page.getByLabel('Email').fill('invalid-email');
  await page.getByLabel('Пароль').fill('demo12345');
  await page.locator('form').getByRole('button', { name: 'Создать аккаунт' }).click();
  await expectVisible(page.getByText('Введите корректный email'));
  consoleErrors.length = 0;

  await gotoApp(page, `${frontendUrl}/login`);
  await expectVisible(page.getByRole('heading', { name: 'Вход в аккаунт' }));
  await page.getByLabel('Email').fill(demoAdminEmail);
  await page.getByLabel('Пароль').fill(demoAdminPassword);
  await page.locator('form').getByRole('button', { name: 'Войти' }).click();

  await expectVisible(page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }));
  await gotoApp(page, `${frontendUrl}/admin/interview-types`);
  await expectVisible(page.getByRole('heading', { name: 'Типы собеседований' }));
  await expectVisible(page.getByText('Backend Java-разработчик').first());
  await gotoApp(page, `${frontendUrl}/admin/questions`);
  await expectVisible(page.getByRole('heading', { name: 'Банк вопросов' }));
  await expectVisible(page.getByText('controlled component').first());
  await gotoApp(page, `${frontendUrl}/admin/question-generation-jobs`);
  await expectVisible(page.getByRole('heading', { name: 'Статус генерации вопросов' }));
  await assertLayoutLooksStable(page);

  await page.getByLabel('Аккаунт пользователя').click();
  await page.getByText('Выйти').click();

  await gotoApp(page, `${frontendUrl}/login`);
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Пароль').fill('user123');
  await page.locator('form').getByRole('button', { name: 'Войти' }).click();
  await expectVisible(page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }));
  await expectVisible(page.getByText('Backend Java-разработчик').first());

  await gotoApp(page, `${frontendUrl}/profile`);
  await expectVisible(page.getByRole('heading', { name: 'Иван Кандидат' }));
  const profileMain = page.getByRole('main');
  await expectVisible(profileMain.getByText('user@example.com'));
  await expectVisible(profileMain.getByText('Профиль подготовки'));

  await gotoApp(page, `${frontendUrl}/dashboard`);
  await expectVisible(page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }));
  await assertLayoutLooksStable(page);
  const finishedHistoryRow = page.locator('.MuiListItemButton-root').filter({ hasText: 'Завершено' }).first();
  if (await finishedHistoryRow.isVisible().catch(() => false)) {
    await finishedHistoryRow.click();
    await page.waitForURL(/\/interviews\/\d+\/result/, { timeout: 15_000 });
    await expectVisible(page.getByRole('heading', { name: 'Разбор по критериям' }));
    await assertLayoutLooksStable(page);
    await gotoApp(page, `${frontendUrl}/dashboard`);
    await expectVisible(page.getByRole('heading', { name: /выберите собеседование из банка IMock/i }));
  }
  await page.getByRole('button', { name: 'Новое mock-собеседование' }).click();
  await expectVisible(page.getByRole('heading', { name: 'Настройка интервью', exact: true }));
  await page.getByRole('button', { name: 'Начать интервью' }).click();

  await expectVisible(page.getByRole('heading', { name: 'Backend Java-разработчик' }));
  await assertLayoutLooksStable(page);
  await page.getByPlaceholder('Введите ответ кандидата...').fill('ArrayList основан на массиве, LinkedList на связном списке.');
  await page.getByLabel('Отправить ответ').click();
  await expectVisible(page.getByText('ArrayList основан на массиве'));
  await expectVisible(page.getByText('Этап: Уточнение'));

  if (consoleErrors.length > 0) {
    throw new Error(`Browser console errors:\n${consoleErrors.join('\n')}`);
  }

  await browser.close();
  await cleanup();
  console.log('Playwright e2e passed');
}

main()
  .catch(async (error) => {
    if (currentPage) {
      await currentPage.screenshot({ path: path.join(rootDir, 'e2e-failure.png'), fullPage: true }).catch(() => {});
      const html = await currentPage.content().catch(() => '');
      if (html) fs.writeFileSync(path.join(rootDir, 'e2e-failure.html'), html, 'utf8');
      console.error(`Failure page URL: ${currentPage.url()}`);
    }
    console.error(error);
    await cleanup();
    process.exit(1);
  });
