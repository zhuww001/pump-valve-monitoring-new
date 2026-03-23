import os
from typing import Dict
from ..data_source.manager import DataSourceManager
from ..config import settings

# .env 文件路径（与 main.py 同级）
_ENV_FILE = os.path.join(os.path.dirname(__file__), '../../.env')


def _save_env(updates: Dict[str, str]):
    """将配置持久化到 .env 文件，已存在的 key 覆盖，不存在的追加"""
    env_path = os.path.abspath(_ENV_FILE)
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # 更新已有的 key
    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue
        key = stripped.split('=', 1)[0].strip()
        if key in updates:
            val = updates[key]
            new_lines.append(f'{key}={val}\n')
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # 追加新的 key
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}={val}\n')

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


class DataSourceService:
    """数据源管理服务"""

    @staticmethod
    def get_current_data_source() -> Dict:
        """获取当前数据源配置"""
        try:
            config = {
                "api_base_url": settings.API_BASE_URL,
                "api_token": settings.API_TOKEN,
                "api_endpoint": settings.API_ENDPOINT,
                "mqtt_broker": settings.MQTT_BROKER,
                "mqtt_port": settings.MQTT_PORT,
                "mqtt_username": settings.MQTT_USERNAME,
                "mqtt_password": settings.MQTT_PASSWORD,
                "mqtt_topic": settings.MQTT_TOPIC,
                "mqtt_client_id": settings.MQTT_CLIENT_ID
            }
            return {
                "type": settings.DATA_SOURCE_TYPE,
                "config": config
            }
        except Exception as e:
            print(f"获取数据源配置失败: {e}")
            return {
                "type": "simulate",
                "config": {}
            }
    
    @staticmethod
    def switch_data_source(data_source_type: str, config: Dict = None) -> bool:
        try:
            env_updates: Dict[str, str] = {
                'DATA_SOURCE_TYPE': data_source_type
            }

            # 先更新内存配置，并收集需要持久化的字段
            if config:
                if data_source_type == "api":
                    settings.API_BASE_URL = config.get("api_base_url")
                    settings.API_TOKEN = config.get("api_token")
                    settings.API_ENDPOINT = config.get("api_endpoint", "/api/pump-data")
                    env_updates.update({
                        'API_BASE_URL': config.get("api_base_url") or '',
                        'API_TOKEN': config.get("api_token") or '',
                        'API_ENDPOINT': config.get("api_endpoint", "/api/pump-data"),
                    })
                elif data_source_type == "mqtt":
                    settings.MQTT_BROKER = config.get("mqtt_broker", "localhost")
                    settings.MQTT_PORT = config.get("mqtt_port", 1883)
                    settings.MQTT_USERNAME = config.get("mqtt_username")
                    settings.MQTT_PASSWORD = config.get("mqtt_password")
                    settings.MQTT_TOPIC = config.get("mqtt_topic", "pump-valve/#")
                    settings.MQTT_CLIENT_ID = config.get("mqtt_client_id", "pump-valve-monitor")
                    env_updates.update({
                        'MQTT_BROKER': config.get("mqtt_broker", "localhost"),
                        'MQTT_PORT': str(config.get("mqtt_port", 1883)),
                        'MQTT_USERNAME': config.get("mqtt_username") or '',
                        'MQTT_PASSWORD': config.get("mqtt_password") or '',
                        'MQTT_TOPIC': config.get("mqtt_topic", "pump-valve/#"),
                        'MQTT_CLIENT_ID': config.get("mqtt_client_id", "pump-valve-monitor"),
                    })

            # 持久化到 .env 文件
            _save_env(env_updates)

            # 清除缓存
            from .data_service import DataService
            DataService.clear_cache()

            # 切换数据源
            manager = DataSourceManager()
            success = manager.switch_data_source(data_source_type)

            return success
        except Exception as e:
            print(f"切换数据源失败: {e}")
            return False
