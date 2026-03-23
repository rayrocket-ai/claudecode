/**
 * Manual login script — run this once to generate the session file.
 * Usage: npm run login
 *
 * This opens a visible browser window. Log in to BrokerBay manually,
 * and the session will be saved automatically once you reach the dashboard.
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { config } from '../config';

const SESSION_PATH = path.resolve(config.sessionPath);
const BROKERBAY_URL = 'https://edge.brokerbay.com';
const LOGIN_URL = 'https://authn.honeywell.com/as/mHuzv5EdfY/resume/as/authorization.ping';

async function manualLogin(): Promise<void> {
  const sessionDir = path.dirname(SESSION_PATH);
  if (!fs.existsSync(sessionDir)) {
    fs.mkdirSync(sessionDir, { recursive: true });
  }

  console.log('Launching browser for manual login...');
  console.log('Please log in to BrokerBay when the browser opens.');
  console.log('The session will be saved automatically once you reach the dashboard.\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  await page.goto(LOGIN_URL);

  // Wait for the user to complete login and reach BrokerBay
  console.log('Waiting for you to log in...');
  await page.waitForURL('**/edge.brokerbay.com/**', { timeout: 300000 }); // 5 min timeout
  await page.waitForLoadState('networkidle');

  // Save session
  const state = await context.storageState();
  fs.writeFileSync(SESSION_PATH, JSON.stringify(state, null, 2));

  console.log(`\n✅ Session saved to ${SESSION_PATH}`);
  console.log('You can now close the browser and run: npm run dev');

  await browser.close();
}

manualLogin().catch((err) => {
  console.error('Login failed:', err);
  process.exit(1);
});
