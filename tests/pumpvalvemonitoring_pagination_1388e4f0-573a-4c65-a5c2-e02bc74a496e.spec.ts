
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('PumpValveMonitoring_Pagination_2026-03-12', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:5000/device/device_1/history');

    // Take screenshot
    await page.screenshot({ path: 'pagination_page.png', { fullPage: true } });

    // Select option
    await page.selectOption('select#page-size', '30');

    // Navigate to URL
    await page.goto('http://localhost:5000/device/device_1/history');

    // Take screenshot
    await page.screenshot({ path: 'pagination_page_updated.png', { fullPage: true } });

    // Select option
    await page.selectOption('select#page-size', '30');

    // Select option
    await page.selectOption('select#page-size', '50');

    // Click element
    await page.click('button[onclick="setTimeRange('24h')"]');

    // Take screenshot
    await page.screenshot({ path: 'pagination_with_data.png', { fullPage: true } });

    // Click element
    await page.click('a.page-link:has-text('下一页')');
});