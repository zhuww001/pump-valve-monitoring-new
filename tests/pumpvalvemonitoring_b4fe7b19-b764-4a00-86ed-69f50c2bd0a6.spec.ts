
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('PumpValveMonitoring_2026-03-12', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:5000');

    // Click element
    await page.click('a[href="/device/device_1"]');

    // Click element
    await page.click('button#start-blockage');

    // Take screenshot
    await page.screenshot({ path: 'blockage_simulation.png', { fullPage: true } });

    // Click element
    await page.click('a[href="/device/device_1/history"]');

    // Click element
    await page.click('button#btn-1h');
});