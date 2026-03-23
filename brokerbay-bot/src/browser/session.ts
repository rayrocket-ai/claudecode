import { chromium, Browser, BrowserContext, Page } from 'playwright';
import fs from 'fs';
import path from 'path';
import pino from 'pino';
import { config } from '../config';

const logger = pino({ level: config.logLevel });

const BROKERBAY_URL = 'https://edge.brokerbay.com';
const LOGIN_URL = 'https://authn.honeywell.com/as/mHuzv5EdfY/resume/as/authorization.ping';

let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

function getSessionPath(): string {
  return path.resolve(config.sessionPath);
}

function ensureSessionDir(): void {
  const dir = path.dirname(getSessionPath());
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export async function saveSession(): Promise<void> {
  if (!context) return;
  ensureSessionDir();
  const state = await context.storageState();
  fs.writeFileSync(getSessionPath(), JSON.stringify(state, null, 2));
  logger.info('Session saved');
}

function hasStoredSession(): boolean {
  return fs.existsSync(getSessionPath());
}

export async function initBrowser(): Promise<Page> {
  if (page && !page.isClosed()) return page;

  logger.info('Launching browser...');
  browser = await chromium.launch({
    headless: config.headless,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const contextOptions: Record<string, unknown> = {
    viewport: { width: 1280, height: 800 },
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  };

  if (hasStoredSession()) {
    logger.info('Loading saved session...');
    contextOptions.storageState = getSessionPath();
  }

  context = await browser.newContext(contextOptions);
  page = await context.newPage();

  return page;
}

export async function getPage(): Promise<Page> {
  if (!page || page.isClosed()) {
    return initBrowser();
  }
  return page;
}

export async function isSessionValid(): Promise<boolean> {
  try {
    const p = await getPage();
    await p.goto(BROKERBAY_URL, { waitUntil: 'networkidle', timeout: 30000 });

    const url = p.url();
    if (url.includes('authn.honeywell.com') || url.includes('login') || url.includes('authorization.ping')) {
      logger.info('Session expired — redirect to login detected');
      return false;
    }

    // Check for a known BrokerBay element that indicates we're logged in
    const loggedIn = await p.locator('[data-testid="user-menu"], .bb-header, .navbar').first().isVisible({ timeout: 5000 }).catch(() => false);
    return loggedIn;
  } catch (err) {
    logger.error({ err }, 'Session validity check failed');
    return false;
  }
}

function randomDelay(min = 150, max = 300): Promise<void> {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function login(email: string, password: string): Promise<void> {
  const p = await getPage();
  logger.info('Navigating to login page...');

  await p.goto(LOGIN_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await randomDelay();

  // Handle Honeywell PingFederate SSO form
  // The form may have different field names; try common selectors
  const emailSelectors = ['input[name="pf.username"]', 'input[name="username"]', 'input[type="email"]', '#email', '#username'];
  const passwordSelectors = ['input[name="pf.pass"]', 'input[name="password"]', 'input[type="password"]', '#password'];

  let emailInput = null;
  for (const sel of emailSelectors) {
    emailInput = await p.$(sel);
    if (emailInput) break;
  }

  if (!emailInput) {
    throw new Error('Could not find email input on login page');
  }

  await emailInput.fill(email);
  await randomDelay();

  let passwordInput = null;
  for (const sel of passwordSelectors) {
    passwordInput = await p.$(sel);
    if (passwordInput) break;
  }

  if (!passwordInput) {
    throw new Error('Could not find password input on login page');
  }

  await passwordInput.fill(password);
  await randomDelay();

  // Submit the form
  const submitSelectors = ['button[type="submit"]', 'input[type="submit"]', '.ping-button', '#submit'];
  let submitBtn = null;
  for (const sel of submitSelectors) {
    submitBtn = await p.$(sel);
    if (submitBtn) break;
  }

  if (submitBtn) {
    await submitBtn.click();
  } else {
    await p.keyboard.press('Enter');
  }

  // Wait for BrokerBay to load after SSO redirect
  await p.waitForURL('**/edge.brokerbay.com/**', { timeout: 60000 });
  await p.waitForLoadState('networkidle');

  logger.info('Login successful — saving session');
  await saveSession();
}

export async function ensureAuthenticated(): Promise<Page> {
  const valid = await isSessionValid();
  if (!valid) {
    logger.info('Session invalid, re-authenticating...');
    await login(config.brokerbayEmail, config.brokerbayPassword);
  }
  return getPage();
}

export async function closeBrowser(): Promise<void> {
  if (page && !page.isClosed()) await page.close();
  if (context) await context.close();
  if (browser) await browser.close();
  page = null;
  context = null;
  browser = null;
  logger.info('Browser closed');
}

export { randomDelay, BROKERBAY_URL, LOGIN_URL };
