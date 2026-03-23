from .base import BaseDataSource
from typing import List, Dict, Optional
from datetime import datetime
import paho.mqtt.client as mqtt
import json
import threading
import time
from collections import defaultdict
from ..config import settings


class MqttDataSource(BaseDataSource):
    """MQTT数据源"""
    
    # 类变量，用于存储全局设备列表
    _global_devices = []
    # 类变量，用于存储全局实时数据
    _global_realtime_data = {}
    # 类变量，用于存储全局历史数据
    _global_history_data = defaultdict(list)
    
    def __init__(self):
        """初始化MQTT数据源"""
        self.broker_address = settings.MQTT_BROKER  # MQTT broker地址
        self.broker_port = settings.MQTT_PORT  # MQTT broker端口
        self.username = settings.MQTT_USERNAME  # MQTT用户名（如果需要）
        self.password = settings.MQTT_PASSWORD  # MQTT密码（如果需要）
        self.client_id = settings.MQTT_CLIENT_ID
        self.topic = settings.MQTT_TOPIC  # 订阅主题，支持通配符
        
        # 存储实时数据，使用全局实时数据
        self.realtime_data = MqttDataSource._global_realtime_data
        # 存储历史数据，使用全局历史数据
        self.history_data = MqttDataSource._global_history_data
        # 设备列表，使用全局设备列表
        self.devices = MqttDataSource._global_devices
        
        # 初始化MQTT客户端
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        # 连接到MQTT broker
        self._connect()
        
        # 启动MQTT客户端线程
        self.thread = threading.Thread(target=self._run_client)
        self.thread.daemon = True
        self.thread.start()
        
        # 初始化设备列表（如果全局设备列表为空）
        if not self.devices:
            self._initialize_devices()
    
    def _connect(self):
        """连接到MQTT broker"""
        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.broker_address, self.broker_port, 60)
            print(f"Connected to MQTT broker at {self.broker_address}:{self.broker_port}")
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            print("MQTT connection successful")
            # 订阅主题
            client.subscribe(self.topic)
            print(f"Subscribed to topic: {self.topic}")
        else:
            print(f"MQTT connection failed with code {rc}")
    
    def _on_message(self, client, userdata, message):
        """MQTT消息回调"""
        try:
            # 解析消息
            payload = message.payload.decode('utf-8')
            print(f"Received MQTT message: {payload}")
            data = json.loads(payload)
            
            # 提取设备ID
            device_id = None
            
            # 处理用户提供的格式: {"${ID}": [{"values": {...}, "ts": ...}]}
            if len(data) == 1:
                # 提取唯一的键作为设备ID
                device_id = list(data.keys())[0]
                print(f"Extracted device ID: {device_id}")
                # 获取数据列表
                data_list = data[device_id]
                if data_list and isinstance(data_list, list):
                    # 获取第一个数据项
                    data_item = data_list[0]
                    # 从values字段提取传感器数据
                    if 'values' in data_item:
                        values = data_item['values']
                        pressure = values.get('pressure', 0)
                        flow = values.get('flow', 0)
                        temperature = values.get('temperature', 0)
                    else:
                        # 回退到直接从数据项中提取
                        pressure = data_item.get('pressure', 0)
                        flow = data_item.get('flow', 0)
                        temperature = data_item.get('temperature', 0)
            else:
                # 处理传统格式
                device_id = data.get('device_id')
                if not device_id:
                    # 从主题中提取设备ID
                    topic_parts = message.topic.split('/')
                    if len(topic_parts) >= 2:
                        device_id = topic_parts[1]
                    else:
                        return
                pressure = data.get('pressure', 0)
                flow = data.get('flow', 0)
                temperature = data.get('temperature', 0)
            
            if not device_id:
                print("No device ID found in message")
                return
            
            # 过滤掉无效设备ID（如<EOF>）
            if device_id in ['<EOF>', 'EOF', '']:
                print(f"Ignoring invalid device ID: {device_id}")
                return
            
            print(f"Processing data for device: {device_id}, pressure: {pressure}, flow: {flow}, temperature: {temperature}")
            
            # 更新实时数据
            self.realtime_data[device_id] = {
                'device_id': device_id,
                'pressure': pressure,
                'flow': flow,
                'temperature': temperature,
                'timestamp': datetime.now().isoformat()
            }
            print(f"Updated realtime data for device {device_id}: {self.realtime_data[device_id]}")
            
            # 存储历史数据
            self.history_data[device_id].append({
                'device_id': device_id,
                'pressure': pressure,
                'flow': flow,
                'temperature': temperature,
                'timestamp': datetime.now().isoformat()
            })
            
            # 限制历史数据长度
            if len(self.history_data[device_id]) > 1000:
                self.history_data[device_id] = self.history_data[device_id][-1000:]
            
            # 更新设备列表
            if device_id not in [d['device_id'] for d in self.devices]:
                self.devices.append({
                    'device_id': device_id,
                    'name': f"设备 {device_id}",
                    'status': 'online'
                })
            
            print(f"Received data from device {device_id}: pressure={pressure}, flow={flow}, temperature={temperature}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def _run_client(self):
        """运行MQTT客户端"""
        try:
            self.client.loop_forever()
        except Exception as e:
            print(f"MQTT client error: {e}")
            # 尝试重连
            time.sleep(5)
            self._connect()
            self._run_client()
    
    def _initialize_devices(self):
        """初始化设备列表"""
        # 这里可以从配置或数据库中加载设备列表
        # 暂时添加一些默认设备
        default_devices = [
            {'device_id': 'Device-1', 'name': '设备 1', 'status': 'offline'},
            {'device_id': 'Device-2', 'name': '设备 2', 'status': 'offline'},
            {'device_id': 'Device-3', 'name': '设备 3', 'status': 'offline'}
        ]
        # 使用extend方法添加默认设备，而不是覆盖全局设备列表
        self.devices.extend(default_devices)
    
    def get_realtime_data(self, device_id: str) -> Dict:
        """获取实时数据"""
        if not device_id:
            print("Device ID is None or empty")
            # 返回默认数据
            return {
                'device_id': device_id,
                'pressure': 0,
                'flow': 0,
                'temperature': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # 过滤掉无效设备ID（如<EOF>）
        if device_id in ['<EOF>', 'EOF', '']:
            print(f"Ignoring invalid device ID: {device_id}")
            return {
                'device_id': device_id,
                'pressure': 0,
                'flow': 0,
                'temperature': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"Current realtime_data: {self.realtime_data}")
        print(f"Getting realtime data for device: {device_id}")
        data = self.realtime_data.get(device_id, {})
        if not data:
            print(f"No data found for device: {device_id}")
            # 返回默认数据
            return {
                'device_id': device_id,
                'pressure': 0,
                'flow': 0,
                'temperature': 0,
                'timestamp': datetime.now().isoformat()
            }
        print(f"Found data for device {device_id}: {data}")
        return data
    
    def get_history_data(self, device_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史数据"""
        # 过滤掉无效设备ID（如<EOF>）
        if device_id in ['<EOF>', 'EOF', '']:
            print(f"Ignoring invalid device ID for history: {device_id}")
            return []
        
        device_history = self.history_data.get(device_id, [])
        # 过滤时间范围
        filtered_data = []
        for data in device_history:
            data_time = datetime.fromisoformat(data['timestamp'])
            if start_time <= data_time <= end_time:
                filtered_data.append(data)
        return filtered_data
    
    def get_device_list(self) -> List[Dict]:
        """获取设备列表"""
        # 过滤掉无效设备（如<EOF>）
        valid_devices = [d for d in self.devices if d.get('device_id') not in ['<EOF>', 'EOF', '']]
        print(f"返回设备列表: {valid_devices}")
        return valid_devices
