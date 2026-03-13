
import { test } from '@playwright/test';
import { expect } from '@playwright/test';

test('PumpValveMonitoring_2026-03-11', async ({ page, context }) => {
  
    // Navigate to URL
    await page.goto('http://localhost:5000');

    // Wait for page to load completely
    await page.waitForLoadState('networkidle');

    // Check page title
    await expect(page).toHaveTitle('泵阀管道堵塞预警系统');

    // Check if real-time data section exists
    const realTimeData = page.locator('#real-time-data');
    await expect(realTimeData).toBeVisible();

    // Check if trend charts section exists
    const trendCharts = page.locator('#trend-charts');
    await expect(trendCharts).toBeVisible();

    // Check if controls section exists
    const controls = page.locator('#controls');
    await expect(controls).toBeVisible();

    // Click start blockage simulation button
    const startButton = page.locator('button:has-text('开始堵塞模拟')');
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Wait for 60 seconds to allow system to detect anomaly
    await page.waitForTimeout(60000);

    // Check if alert is generated
    const alertInfo = page.locator('#alert-info');
    await expect(alertInfo).toContainText('预警');

    // Click stop blockage simulation button
    const stopButton = page.locator('button:has-text('停止堵塞模拟')');
    await expect(stopButton).toBeVisible();
    await stopButton.click();

    // Wait for 30 seconds to allow system to return to normal
    await page.waitForTimeout(30000);

    // Check if alert is cleared
    await expect(alertInfo).not.toContainText('预警');
});