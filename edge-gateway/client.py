#!/usr/bin/env python3
"""
边缘网关客户端模拟器
用于模拟传感器数据采集和上报
"""

import asyncio
import aiohttp
import random
from datetime import datetime
import json
import time


class EdgeGatewayClient:
    """边缘网关客户端"""
    
    def __init__(self, gateway_id: str, main_system_url: str = "http://localhost:8001"):
        self.gateway_id = gateway_id
        self.main_system_url = main_system_url
        self.upload_endpoint = f"{main_system_url}/api/data/upload"
        self.running = False
        
        # 模拟3个传感器设备
        self.devices = [
            {"device_id": "device_1", "name": "一号泵阀传感器"},
            {"device_id": "device_2", "name": "二号泵阀传感器"},
            {"device_id": "device_3", "name": "三号泵阀传感器"}
        ]
    
    async def collect_sensor_data(self, device_id: str) -> dict:
        """
        采集传感器数据
        模拟从实际传感器读取数据
        """
        # 模拟传感器读数（带有一些随机波动）
        pressure = round(random.uniform(0.8, 1.5), 2)
        flow = round(random.uniform(8.0, 15.0), 2)
        temperature = round(random.uniform(35.0, 50.0), 2)
        
        # 偶尔生成异常数据（用于测试预警功能）
        if random.random() < 0.1:  # 10%概率生成异常
            pressure = round(random.uniform(2.1, 2.5), 2)  # 压力过高
        
        return {
            "device_id": device_id,
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "pressure": pressure,
            "flow": flow,
            "temperature": temperature,
            "status": "normal",
            "source_type": "edge_gateway"
        }
    
    async def upload_data(self, session: aiohttp.ClientSession, sensors_data: list):
        """
        上传数据到主系统
        """
        payload = {
            "gateway_id": self.gateway_id,
            "timestamp": datetime.now().isoformat(),
            "sensors": sensors_data
        }
        
        try:
            async with session.post(self.upload_endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    sensor_count = len(sensors_data)
                    print(f"✓ 数据上传成功: {sensor_count} 个传感器")
                    return True
                else:
                    print(f"✗ 数据上传失败: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"✗ 数据上传异常: {e}")
            return False
    
    async def run(self, interval: int = 5):
        """
        运行边缘网关客户端
        
        Args:
            interval: 数据采集间隔（秒）
        """
        self.running = True
        print(f"边缘网关 {self.gateway_id} 启动")
        print(f"数据采集间隔: {interval}秒")
        print(f"目标系统: {self.main_system_url}")
        print("-" * 50)
        
        async with aiohttp.ClientSession() as session:
            while self.running:
                try:
                    # 采集所有传感器数据
                    sensors_data = []
                    for device in self.devices:
                        data = await self.collect_sensor_data(device["device_id"])
                        sensors_data.append(data)
                        print(f"  采集 [{device['name']}]: 压力={data['pressure']}, 流量={data['flow']}, 温度={data['temperature']}")
                    
                    # 上传数据
                    await self.upload_data(session, sensors_data)
                    
                    # 等待下一次采集
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    print(f"运行异常: {e}")
                    await asyncio.sleep(interval)
    
    def stop(self):
        """停止客户端"""
        self.running = False
        print(f"边缘网关 {self.gateway_id} 停止")


async def main():
    """主函数"""
    # 创建边缘网关客户端
    client = EdgeGatewayClient(
        gateway_id="gateway_001",
        main_system_url="http://localhost:8001"
    )
    
    try:
        # 运行客户端（每5秒采集一次数据）
        await client.run(interval=5)
    except KeyboardInterrupt:
        print("\n接收到停止信号")
        client.stop()


if __name__ == "__main__":
    print("=" * 50)
    print("边缘网关客户端模拟器")
    print("=" * 50)
    print()
    
    # 运行异步主函数
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
