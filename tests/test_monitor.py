import asyncio
import time
import requests
import os
import csv
from datetime import datetime

class TestMonitor:
    def __init__(self):
        self.mock_api_url = "http://localhost:8000/api/pump-data"
        self.set_mode_url = "http://localhost:8000/api/set-mode"
    
    def test_api_connectivity(self):
        """测试接口连通性"""
        print("=== 测试接口连通性 ===")
        try:
            response = requests.get(self.mock_api_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    print("✓ 接口连通成功")
                    print(f"  数据示例: {data['data']}")
                    return True
                else:
                    print(f"✗ 接口返回错误: {data['msg']}")
                    return False
            else:
                print(f"✗ 接口请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 接口连通异常: {str(e)}")
            return False
    
    def test_normal_conditions(self):
        """测试正常工况"""
        print("\n=== 测试正常工况 ===")
        
        # 设置为正常模式
        try:
            response = requests.post(self.set_mode_url, params={"mode": "normal"})
            if response.status_code == 200:
                print("✓ 已设置为正常模式")
            else:
                print("✗ 设置模式失败")
                return False
        except Exception as e:
            print(f"✗ 设置模式异常: {str(e)}")
            return False
        
        # 采集10条数据，检查是否正常
        normal_data = []
        for i in range(10):
            try:
                response = requests.get(self.mock_api_url, timeout=3)
                if response.status_code == 200:
                    data = response.json()['data']
                    normal_data.append(data)
                    print(f"  采集数据 {i+1}: 压力={data['pressure']}, 流量={data['flow']}")
                else:
                    print(f"  采集数据 {i+1} 失败")
            except Exception as e:
                print(f"  采集数据 {i+1} 异常: {str(e)}")
            time.sleep(1)
        
        # 检查数据是否在合理范围内
        if normal_data:
            pressures = [d['pressure'] for d in normal_data]
            flows = [d['flow'] for d in normal_data]
            
            pressure_avg = sum(pressures) / len(pressures)
            flow_avg = sum(flows) / len(flows)
            
            pressure_max = max(pressures)
            pressure_min = min(pressures)
            flow_max = max(flows)
            flow_min = min(flows)
            
            print(f"\n  压力范围: {pressure_min:.2f} - {pressure_max:.2f} MPa")
            print(f"  流量范围: {flow_min:.1f} - {flow_max:.1f} m³/h")
            print(f"  压力平均值: {pressure_avg:.2f} MPa")
            print(f"  流量平均值: {flow_avg:.1f} m³/h")
            
            # 检查波动是否在正常范围内
            pressure_variation = (pressure_max - pressure_min) / pressure_avg * 100
            flow_variation = (flow_max - flow_min) / flow_avg * 100
            
            if pressure_variation < 5 and flow_variation < 5:
                print("✓ 正常工况数据波动在合理范围内")
                return True
            else:
                print(f"✗ 数据波动过大: 压力{pressure_variation:.1f}%, 流量{flow_variation:.1f}%")
                return False
        else:
            print("✗ 未采集到正常工况数据")
            return False
    
    def test_blockage_conditions(self):
        """测试堵塞工况"""
        print("\n=== 测试堵塞工况 ===")
        
        # 设置为堵塞模式
        try:
            response = requests.post(self.set_mode_url, params={"mode": "blockage"})
            if response.status_code == 200:
                print("✓ 已设置为堵塞模式")
            else:
                print("✗ 设置模式失败")
                return False
        except Exception as e:
            print(f"✗ 设置模式异常: {str(e)}")
            return False
        
        # 采集20条数据，观察压力上升和流量下降趋势
        blockage_data = []
        for i in range(20):
            try:
                response = requests.get(self.mock_api_url, timeout=3)
                if response.status_code == 200:
                    data = response.json()['data']
                    blockage_data.append(data)
                    print(f"  采集数据 {i+1}: 压力={data['pressure']}, 流量={data['flow']}")
                else:
                    print(f"  采集数据 {i+1} 失败")
            except Exception as e:
                print(f"  采集数据 {i+1} 异常: {str(e)}")
            time.sleep(1)
        
        # 检查趋势
        if len(blockage_data) >= 10:
            # 计算前5条和后5条的平均值
            first_five = blockage_data[:5]
            last_five = blockage_data[-5:]
            
            first_pressure_avg = sum(d['pressure'] for d in first_five) / len(first_five)
            last_pressure_avg = sum(d['pressure'] for d in last_five) / len(last_five)
            
            first_flow_avg = sum(d['flow'] for d in first_five) / len(first_five)
            last_flow_avg = sum(d['flow'] for d in last_five) / len(last_five)
            
            pressure_change = (last_pressure_avg - first_pressure_avg) / first_pressure_avg * 100
            flow_change = (last_flow_avg - first_flow_avg) / first_flow_avg * 100
            
            print(f"\n  压力变化: {pressure_change:.1f}%")
            print(f"  流量变化: {flow_change:.1f}%")
            
            if pressure_change > 5 and flow_change < -5:
                print("✓ 堵塞工况数据趋势正确")
                return True
            else:
                print("✗ 堵塞工况数据趋势不正确")
                return False
        else:
            print("✗ 未采集到足够的堵塞工况数据")
            return False
    
    def test_alert_logging(self):
        """测试预警日志"""
        print("\n=== 测试预警日志 ===")
        
        alert_log_path = "logs/alert_log.csv"
        if os.path.exists(alert_log_path):
            with open(alert_log_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            if len(rows) > 1:  # 至少有表头和一条记录
                print(f"✓ 预警日志文件存在，包含 {len(rows)-1} 条预警记录")
                print("  最新预警记录:")
                for row in rows[-2:]:  # 显示最后两条记录
                    print(f"    {row}")
                return True
            else:
                print("✗ 预警日志文件存在，但无预警记录")
                return False
        else:
            print("✗ 预警日志文件不存在")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始测试泵阀管道堵塞预警系统...")
        
        tests = [
            ("接口连通性测试", self.test_api_connectivity),
            ("正常工况测试", self.test_normal_conditions),
            ("堵塞工况测试", self.test_blockage_conditions),
            ("预警日志测试", self.test_alert_logging)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        
        print(f"\n=== 测试结果 ===")
        print(f"通过: {passed}/{total}")
        
        if passed == total:
            print("✓ 所有测试通过！")
        else:
            print("✗ 部分测试失败，请检查系统配置")

if __name__ == "__main__":
    tester = TestMonitor()
    tester.run_all_tests()
