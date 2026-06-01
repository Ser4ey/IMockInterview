import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const frontendUrl = process.env.IMOCK_FRONTEND_URL || 'http://127.0.0.1:15190';
const backendUrl = process.env.IMOCK_BACKEND_URL || 'http://127.0.0.1:18110';
const screenshotsDir = path.resolve('..', 'screenshots', 'vkr');

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
| fig_02_home_page.png | Рисунок 2 – Главная страница веб-сервиса IMock | Основная часть |
| fig_03_interview_setup.png | Рисунок 3 – Экран выбора параметров интервью | Основная часть |
| fig_04_interview_chat.png | Рисунок 4 – Интерфейс чата с ИИ-интервьюером | Основная часть |
| fig_05_interview_result.png | Рисунок 5 – Экран результата собеседования | Основная часть |
| fig_06_dashboard.png | Рисунок 6 – Личный кабинет пользователя | Основная часть |
| fig_B01_home_page.png | Рисунок Б – 1. Главная страница | Приложение Б |
| fig_B02_registration.png | Рисунок Б – 2. Страница регистрации | Приложение Б |
| fig_B03_interview_setup.png | Рисунок Б – 3. Страница выбора интервью | Приложение Б |
| fig_B04_interview_chat.png | Рисунок Б – 4. Чат интервью | Приложение Б |
| fig_B05_interview_result.png | Рисунок Б – 5. Экран результата | Приложение Б |
| fig_B06_dashboard.png | Рисунок Б – 6. Личный кабинет | Приложение Б |
`;
  fs.writeFileSync(path.join(screenshotsDir, 'README.md'), readme, 'utf8');
}

async function main() {
  fs.mkdirSync(screenshotsDir, { recursive: true });

  const token = await loginDemoUser();
  const sessions = await apiJson('/interviews', token);
  const chatSession = sessions.find((session) => session.status === 'active')
    ?? sessions.find((session) => session.interview_type_title?.includes('Backend'));
  const resultSession = sessions.find((session) => session.status === 'finished' && session.interview_type_title?.includes('Backend'))
    ?? sessions.find((session) => session.status === 'finished');

  if (!chatSession || !resultSession) {
    throw new Error('Не найдены demo-интервью для чата и результата. Запустите backend/scripts/seed_demo.py.');
  }

  const browser = await chromium.launch({ headless: true });
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

  await context.addInitScript((value) => {
    localStorage.setItem('token', value);
  }, token);
  const authPage = await context.newPage();

  await gotoApp(authPage, '/dashboard');
  await waitVisible(authPage.getByRole('heading', { name: /продолжим тренировать собеседования/i }));
  await take(authPage, 'fig_06_dashboard.png');

  await authPage.evaluate(() => window.scrollTo(0, 260));
  await take(authPage, 'fig_B06_dashboard.png');

  await authPage.evaluate(() => window.scrollTo(0, 0));
  await authPage.getByRole('button', { name: 'Новое mock-собеседование' }).click();
  await waitVisible(authPage.getByRole('heading', { name: 'Настройка интервью', exact: true }));
  await take(authPage, 'fig_03_interview_setup.png');
  await take(authPage, 'fig_B03_interview_setup.png');
  await authPage.keyboard.press('Escape');

  await gotoApp(authPage, `/interviews/${chatSession.id}`);
  await waitVisible(authPage.getByRole('heading', { name: chatSession.interview_type_title }));
  await waitVisible(authPage.getByText('Расскажите, пожалуйста, как устроена архитектура REST API'));
  await authPage.getByPlaceholder('Введите ответ кандидата...').fill('Я бы добавил cursor-based пагинацию и ограничение размера страницы.');
  await take(authPage, 'fig_04_interview_chat.png');
  await take(authPage, 'fig_B04_interview_chat.png');

  await gotoApp(authPage, `/interviews/${resultSession.id}/result`);
  await waitVisible(authPage.getByRole('heading', { name: 'Разбор по критериям' }));
  await take(authPage, 'fig_05_interview_result.png');

  await authPage.evaluate(() => window.scrollTo(0, 320));
  await take(authPage, 'fig_B05_interview_result.png');

  writeReadme();
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
