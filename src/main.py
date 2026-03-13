import asyncio
import time
import json
import csv
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime
import yaml
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lstm_detector import LSTMAnomalyDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PumpValveMonitor:
    def __init__(self, config_path, device_config):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 设备配置
        self.device_id = device_config['id']
        self.device_name = device_config['name']
        self.device_location = device_config['location']
        self.device_api_url = device_config['mock_api_url']
        
        # 初始化数据存储
        self.raw_data = []
        self.baseline_data = []
        self.alert_count = 0
        self.consecutive_alerts = 0
        
        # 初始基准值（使用设备配置中的初始基准值）
        self.initial_baseline_pressure = device_config['initial_baseline']['pressure']
        self.initial_baseline_flow = device_config['initial_baseline']['flow']
        
        # 初始化LSTM异常检测器
        self.lstm_detector = LSTMAnomalyDetector()
        
        # 确保存储目录存在
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # 初始化CSV文件
        self.init_csv_files()
    
    def init_csv_files(self):
        # 初始化原始数据CSV
        raw_data_path = f"data/raw_data_{self.device_id}.csv"
        if not os.path.exists(raw_data_path):
            with open(raw_data_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_id', 'device_name', 'location', 'timestamp', 'pressure', 'flow', 'valve_open', 'temperature'])
        
        # 初始化预警日志CSV
        alert_log_path = f"logs/alert_log_{self.device_id}.csv"
        if not os.path.exists(alert_log_path):
            with open(alert_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['device_id', 'device_name', 'location', 'timestamp', 'alert_level', 'message', 'pressure', 'flow', 'baseline_pressure', 'baseline_flow'])
    
    async def collect_data(self):
        """采集数据"""
        api_url = self.device_api_url
        timeout = self.config['data_collection']['api']['timeout']
        max_retries = self.config['data_collection']['api']['max_retries']
        
        for attempt in range(max_retries):
            try:
                response = requests.get(api_url, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 200:
                        return data['data']
                    else:
                        logger.error(f"设备 {self.device_id} 接口返回错误: {data['msg']}")
                else:
                    logger.error(f"设备 {self.device_id} 接口请求失败: {response.status_code}")
            except Exception as e:
                logger.error(f"设备 {self.device_id} 数据采集异常: {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info(f"设备 {self.device_id} 重试中... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(1)
        
        return None
    
    def preprocess_data(self, data):
        """预处理数据"""
        # 添加设备信息
        data['device_id'] = self.device_id
        data['device_name'] = self.device_name
        data['location'] = self.device_location
        
        # 处理缺失值
        for key in ['pressure', 'flow', 'valve_open', 'temperature']:
            if key not in data:
                data[key] = None
        
        # 存储原始数据
        self.raw_data.append(data)
        
        # 保存到CSV
        self.save_to_csv(data)
        
        return data
    
    def save_to_csv(self, data):
        """保存数据到CSV"""
        raw_data_path = f"data/raw_data_{self.device_id}.csv"
        with open(raw_data_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['device_id'],
                data['device_name'],
                data['location'],
                data['timestamp'],
                data.get('pressure', ''),
                data.get('flow', ''),
                data.get('valve_open', ''),
                data.get('temperature', '')
            ])
    
    def calculate_baseline(self):
        """计算基准值"""
        # 只使用最近1分钟的数据
        window_size = self.config['data_preprocessing']['baseline_window'] * 6  # 10秒一条，1分钟=6条
        recent_data = self.raw_data[-window_size:]
        
        logger.info(f"设备 {self.device_id} 当前原始数据长度: {len(self.raw_data)}, 最近数据长度: {len(recent_data)}")
        
        if len(recent_data) < 3:  # 至少需要3条数据
            logger.info(f"设备 {self.device_id} 数据不足，需要至少3条，当前只有{len(recent_data)}条")
            return None, None
        
        pressures = [d['pressure'] for d in recent_data if d['pressure'] is not None]
        flows = [d['flow'] for d in recent_data if d['flow'] is not None]
        
        if not pressures or not flows:
            return None, None
        
        baseline_pressure = np.mean(pressures)
        baseline_flow = np.mean(flows)
        
        return baseline_pressure, baseline_flow
    
    def detect_anomaly(self, data, baseline_pressure, baseline_flow):
        """检测异常"""
        if baseline_pressure is None or baseline_flow is None:
            return False, ""
        
        pressure = data.get('pressure')
        flow = data.get('flow')
        
        if pressure is None or flow is None:
            return False, ""
        
        # 优先使用LSTM模型进行异常检测
        if len(self.raw_data) >= 10:  # LSTM需要至少10条历史数据
            is_lstm_anomaly, confidence = self.lstm_detector.detect_anomaly(self.raw_data)
            if is_lstm_anomaly:
                logger.info(f"设备 {self.device_id} LSTM模型检测到异常，置信度: {confidence:.4f}")
                self.consecutive_alerts += 1
                message = f"LSTM模型检测到异常，置信度: {confidence:.4f}"
                logger.info(f"设备 {self.device_id} 触发阈值，连续次数: {self.consecutive_alerts}")
            else:
                self.consecutive_alerts = 0
                message = ""
                logger.info(f"设备 {self.device_id} LSTM模型未检测到异常，连续次数重置为0")
        else:
            # 使用传统统计方法
            # 计算相对变化
            pressure_change = (pressure - baseline_pressure) / baseline_pressure * 100
            flow_change = (flow - baseline_flow) / baseline_flow * 100
            
            # 检查是否触发阈值
            pressure_threshold = self.config['anomaly_detection']['pressure_threshold']
            flow_threshold = self.config['anomaly_detection']['flow_threshold']
            
            logger.info(f"设备 {self.device_id} 当前数据: 压力={pressure}MPa, 流量={flow}m³/h")
            logger.info(f"设备 {self.device_id} 基准数据: 压力={baseline_pressure:.2f}MPa, 流量={baseline_flow:.1f}m³/h")
            logger.info(f"设备 {self.device_id} 变化率: 压力={pressure_change:.2f}%, 流量={flow_change:.2f}%")
            logger.info(f"设备 {self.device_id} 阈值: 压力≥{pressure_threshold}%, 流量≤-{flow_threshold}%")
            
            if pressure_change >= pressure_threshold and flow_change <= -flow_threshold:
                self.consecutive_alerts += 1
                message = f"压力上升 {pressure_change:.2f}%，流量下降 {abs(flow_change):.2f}%"
                logger.info(f"设备 {self.device_id} 触发阈值，连续次数: {self.consecutive_alerts}")
            else:
                self.consecutive_alerts = 0
                message = ""
                logger.info(f"设备 {self.device_id} 未触发阈值，连续次数重置为0")
        
        # 检查连续触发次数
        consecutive_triggers = self.config['anomaly_detection']['consecutive_triggers']
        if self.consecutive_alerts >= consecutive_triggers:
            logger.info(f"设备 {self.device_id} 连续触发{self.consecutive_alerts}次，超过阈值{consecutive_triggers}次，生成预警")
            return True, message
        
        logger.info(f"设备 {self.device_id} 连续触发{self.consecutive_alerts}次，未达到阈值{consecutive_triggers}次，不生成预警")
        return False, message
    
    def generate_alert(self, data, message, baseline_pressure, baseline_flow):
        """生成预警"""
        alert_level = "紧急预警" if self.consecutive_alerts >= 5 else "一般预警"
        timestamp = data['timestamp']
        
        # 记录预警
        alert_log = {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'location': self.device_location,
            'timestamp': timestamp,
            'alert_level': alert_level,
            'message': message,
            'pressure': data.get('pressure', ''),
            'flow': data.get('flow', ''),
            'baseline_pressure': baseline_pressure,
            'baseline_flow': baseline_flow
        }
        
        # 保存到预警日志
        alert_log_path = f"logs/alert_log_{self.device_id}.csv"
        with open(alert_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                alert_log['device_id'],
                alert_log['device_name'],
                alert_log['location'],
                alert_log['timestamp'],
                alert_log['alert_level'],
                alert_log['message'],
                alert_log['pressure'],
                alert_log['flow'],
                alert_log['baseline_pressure'],
                alert_log['baseline_flow']
            ])
        
        # 输出预警信息
        logger.warning(f"设备 {self.device_id} [{alert_level}] {timestamp} - {message}")
        print(f"设备 {self.device_id} [{alert_level}] {timestamp} - {message}")
        
        # 发送短信通知
        self.send_sms_alert(alert_level, message, timestamp)
        
        self.alert_count += 1
    
    def send_sms_alert(self, alert_level, message, timestamp):
        """发送短信预警"""
        # 检查是否启用短信通知
        if not self.config['alert']['output'].get('sms', False):
            return
        
        # 获取短信配置
        sms_config = self.config['alert']['sms']
        provider = sms_config['provider']
        recipients = sms_config['recipients']
        template = sms_config['template']
        
        # 生成短信内容
        sms_content = template.format(
            alert_level=alert_level,
            message=f"{self.device_name}({self.device_location}) {message}",
            timestamp=timestamp
        )
        
        # 根据提供商发送短信
        if provider == 'simulation':
            # 模拟发送
            self._send_sms_simulation(recipients, sms_content, sms_config['simulation'])
        elif provider == 'twilio':
            # 使用Twilio发送（示例）
            self._send_sms_twilio(recipients, sms_content, sms_config['twilio'])
        elif provider == 'aliyun':
            # 使用阿里云发送（示例）
            self._send_sms_aliyun(recipients, sms_content, sms_config['aliyun'])
    
    def _send_sms_simulation(self, recipients, content, config):
        """模拟发送短信"""
        if config.get('enabled', True):
            delay = config.get('delay', 1)
            logger.info(f"[模拟短信] 准备发送短信，延迟{delay}秒...")
            time.sleep(delay)
            for recipient in recipients:
                logger.info(f"[模拟短信] 发送到 {recipient}: {content}")
                print(f"[模拟短信] 发送到 {recipient}: {content}")
    
    def _send_sms_twilio(self, recipients, content, config):
        """使用Twilio发送短信"""
        try:
            from twilio.rest import Client
            
            account_sid = config['account_sid']
            auth_token = config['auth_token']
            from_number = config['from_number']
            
            client = Client(account_sid, auth_token)
            for recipient in recipients:
                message = client.messages.create(
                    body=content,
                    from_=from_number,
                    to=recipient
                )
                logger.info(f"[Twilio] 短信发送成功，消息ID: {message.sid}")
        except Exception as e:
            logger.error(f"[Twilio] 短信发送失败: {str(e)}")
    
    def _send_sms_aliyun(self, recipients, content, config):
        """使用阿里云发送短信"""
        try:
            from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
            from alibabacloud_tea_openapi import models as open_api_models
            
            access_key_id = config['access_key_id']
            access_key_secret = config['access_key_secret']
            sign_name = config['sign_name']
            template_code = config['template_code']
            
            config = open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )
            config.endpoint = 'dysmsapi.aliyuncs.com'
            client = Dysmsapi20170525Client(config)
            
            for recipient in recipients:
                send_sms_request = models.SendSmsRequest(
                    phone_numbers=recipient,
                    sign_name=sign_name,
                    template_code=template_code,
                    template_param=json.dumps({"content": content})
                )
                response = client.send_sms(send_sms_request)
                logger.info(f"[阿里云] 短信发送成功，响应: {response.body}")
        except Exception as e:
            logger.error(f"[阿里云] 短信发送失败: {str(e)}")
    
    async def run(self):
        """运行监控"""
        logger.info(f"设备 {self.device_id} 监控启动")
        
        collection_interval = self.config['data_collection']['collection_interval']
        logger.info(f"设备 {self.device_id} 采集间隔: {collection_interval}秒")
        logger.info(f"设备 {self.device_id} 初始基准值: 压力={self.initial_baseline_pressure}MPa, 流量={self.initial_baseline_flow}m³/h")
        
        while True:
            logger.info(f"设备 {self.device_id} 开始采集数据...")
            # 采集数据
            data = await self.collect_data()
            if data:
                logger.info(f"设备 {self.device_id} 成功采集数据: {data}")
                # 预处理数据
                processed_data = self.preprocess_data(data)
                logger.info(f"设备 {self.device_id} 数据预处理完成")
                
                # 计算基准值
                baseline_pressure, baseline_flow = self.calculate_baseline()
                if baseline_pressure is None or baseline_flow is None:
                    logger.info(f"设备 {self.device_id} 基准值计算中，数据不足")
                else:
                    logger.info(f"设备 {self.device_id} 计算基准值: 压力={baseline_pressure:.2f}MPa, 流量={baseline_flow:.1f}m³/h")
                
                # 检测异常（使用初始基准值进行比较，提高敏感性）
                is_anomaly, message = self.detect_anomaly(processed_data, self.initial_baseline_pressure, self.initial_baseline_flow)
                if is_anomaly:
                    logger.info(f"设备 {self.device_id} 检测到异常: {message}")
                    # 生成预警
                    self.generate_alert(processed_data, message, self.initial_baseline_pressure, self.initial_baseline_flow)
                else:
                    logger.info(f"设备 {self.device_id} 未检测到异常")
            else:
                logger.warning(f"设备 {self.device_id} 采集数据失败")
            
            # 等待下一次采集
            logger.info(f"设备 {self.device_id} 等待 {collection_interval} 秒后进行下一次采集")
            await asyncio.sleep(collection_interval)

class DeviceManager:
    def __init__(self, config_path):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化设备监控实例
        self.device_monitors = []
        for device_config in self.config['devices']:
            monitor = PumpValveMonitor(config_path, device_config)
            self.device_monitors.append(monitor)
        
    async def run_all(self):
        """运行所有设备的监控"""
        logger.info(f"启动 {len(self.device_monitors)} 个设备的监控")
        # 创建所有设备的监控任务
        tasks = [monitor.run() for monitor in self.device_monitors]
        # 并行运行所有任务
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    manager = DeviceManager('config/config.yaml')
    asyncio.run(manager.run_all())
