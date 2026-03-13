from playwright.sync_api import Playwright, sync_playwright, expect
import time

def test_pump_valve_monitoring(playwright: Playwright) -> None:
    # 启动浏览器
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    try:
        # 访问Web界面
        page.goto("http://localhost:5000")
        
        # 等待页面加载完成
        page.wait_for_load_state("networkidle")
        
        # 检查页面标题
        expect(page).to_have_title("泵阀管道堵塞预警系统")
        
        # 检查实时数据区域是否存在
        real_time_data = page.locator("#real-time-data")
        expect(real_time_data).to_be_visible()
        
        # 检查趋势图区域是否存在
        trend_charts = page.locator("#trend-charts")
        expect(trend_charts).to_be_visible()
        
        # 检查控制按钮区域是否存在
        controls = page.locator("#controls")
        expect(controls).to_be_visible()
        
        # 点击开始堵塞模拟按钮
        start_button = page.locator("button:has-text('开始堵塞模拟')")
        expect(start_button).to_be_visible()
        start_button.click()
        
        # 等待一段时间，让系统检测到异常
        time.sleep(60)  # 等待1分钟，系统应该在1分钟内检测到异常
        
        # 检查是否生成了预警
        alert_info = page.locator("#alert-info")
        expect(alert_info).to_contain_text("预警")
        
        # 检查趋势图是否显示了异常变化
        # 这里可以添加更详细的趋势图检查逻辑
        
        # 点击停止堵塞模拟按钮
        stop_button = page.locator("button:has-text('停止堵塞模拟')")
        expect(stop_button).to_be_visible()
        stop_button.click()
        
        # 等待一段时间，让系统恢复正常
        time.sleep(30)
        
        # 检查预警是否已解除
        expect(alert_info).to_not_contain_text("预警")
        
    finally:
        # 关闭浏览器
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        test_pump_valve_monitoring(playwright)
