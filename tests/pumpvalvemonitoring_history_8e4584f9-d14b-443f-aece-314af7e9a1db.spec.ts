
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('PumpValveMonitoring_History_2026-03-12', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:5000');

    // Click element
    await page.click('a[href="/device/device_1/history"]');

    // Click element
    await page.click('button[onclick="setTimeRange('1h')"]');

    // Click element
    await page.click('button[onclick="setTimeRange('30m')"]');

    // Navigate to URL
    await page.goto('http://localhost:5000/device/device_1/history');

    // Take screenshot
    await page.screenshot({ path: 'history_page.png', { fullPage: true } });

    // Click element
    await page.click('button[onclick="setTimeRange('30m')"]');

    // Fill input field
    await page.fill('input#start-time', '2026-03-12T09:30');

    // Fill input field
    await page.fill('input#end-time', '2026-03-12T09:45');

    // Click element
    await page.click('button[onclick="applyCustomRange()"]');
});