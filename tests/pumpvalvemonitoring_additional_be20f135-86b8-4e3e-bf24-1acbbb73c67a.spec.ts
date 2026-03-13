
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('PumpValveMonitoring_Additional_2026-03-12', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:5000');

    // Click element
    await page.click('a[href="/device/device_1/edit"]');

    // Fill input field
    await page.fill('input[name="manager"]', '李经理');

    // Fill input field
    await page.fill('input#device-manager', '李经理');

    // Fill input field
    await page.fill('input#device-contact', '13800138008');

    // Click element
    await page.click('button[type="submit"]');

    // Click element
    await page.click('a[href="/device/device_1/alerts"]');

    // Take screenshot
    await page.screenshot({ path: 'alerts_page.png', { fullPage: true } });
});