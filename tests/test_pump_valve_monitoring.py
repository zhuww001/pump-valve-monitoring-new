from playwright.sync_api import sync_playwright, expect
import time

def test_pump_valve_monitoring():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
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
            
            # 等待60秒，让系统检测到异常
            time.sleep(60)
            
            # 检查是否生成了预警
            alert_info = page.locator("#alert-info")
            expect(alert_info).to_contain_text("预警")
            
            # 点击停止堵塞模拟按钮
            stop_button = page.locator("button:has-text('停止堵塞模拟')")
            expect(stop_button).to_be_visible()
            stop_button.click()
            
            # 等待30秒，让系统恢复正常
            time.sleep(30)
            
            # 检查预警是否已解除
            expect(alert_info).not_to_contain_text("预警")
            
            print("测试通过！系统功能正常。")
            
        except Exception as e:
            print(f"测试失败: {e}")
        finally:
            # 关闭浏览器
            browser.close()

if __name__ == "__main__":
    test_pump_valve_monitoring()
