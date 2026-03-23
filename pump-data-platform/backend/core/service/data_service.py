import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..db import get_redis_client, get_influxdb_client
from ..config import settings
from ..data_process.warning_checker import WarningChecker
from ..data_source.manager import DataSourceManager
from .warning_service import WarningService



def _offline_response(device_id: str) -> Dict:
    return {
        "device_id": device_id,
        "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "pressure": 0.0,
        "flow": 0.0,
        "temperature": 0.0,
        "status": "offline",
        "source_type": "unknown",
    }


def _check_status(pressure: float, flow: float, temperature: float) -> str:
    status, _ = WarningChecker.check_warning(
        {"pressure": pressure, "flow": flow, "temperature": temperature}
    )
    return status


class DataService:
    """数据查询服务"""

    # 内存存储，用于接收边缘网关数据
    _received_data_cache: Dict = {}
    
    @staticmethod
    def clear_cache():
        """清除缓存"""
        DataService._received_data_cache.clear()

    @staticmethod
    def get_realtime_data(device_id: str) -> Dict:
        """获取实时数据"""
        print(f"=== 获取实时数据开始: device_id={device_id} ===")
        print(f"当前数据源类型: {settings.DATA_SOURCE_TYPE}")

        # 优先使用设备推送的真实数据（边缘网关/MQTT上报）
        if device_id in DataService._received_data_cache:
            cached = DataService._received_data_cache[device_id]
            # 只有缓存中是真实数据（非模拟）时才优先返回
            if cached.get("source_type") not in ("simulate", "memory_cache"):
                print(f"从推送缓存获取数据: {cached}")
                print("=== 获取实时数据结束 (推送缓存) ===")
                return cached

        # 尝试从数据源管理器获取数据
        try:
            manager = DataSourceManager()
            data_source = manager.get_data_source()
            print(f"使用数据源: {type(data_source).__name__}")
            realtime_data = data_source.get_realtime_data(device_id)
            print(f"从数据源获取的数据: {realtime_data}")

            # 处理数据格式，确保包含所有必要字段
            pressure = realtime_data.get('pressure', 0.0)
            flow = realtime_data.get('flow', 0.0)
            temperature = realtime_data.get('temperature', 0.0)

            # 数据源返回离线/全零时，优先回退到推送缓存
            if realtime_data.get("status") == "offline" and device_id in DataService._received_data_cache:
                cached = DataService._received_data_cache[device_id]
                print(f"数据源返回离线，使用推送缓存: {cached}")
                print("=== 获取实时数据结束 (推送缓存降级) ===")
                return cached

            data = {
                "device_id": device_id,
                "timestamp": realtime_data.get('timestamp', datetime.now().strftime('%Y-%m-%dT%H:%M:%S')),
                "pressure": pressure,
                "flow": flow,
                "temperature": temperature,
                "status": _check_status(pressure, flow, temperature),
                "source_type": "mqtt" if settings.DATA_SOURCE_TYPE == "mqtt" else "simulate",
            }
            print(f"处理后的数据: {data}")

            # 仅当数据源类型为 mqtt 时才更新缓存（避免模拟数据覆盖真实推送数据）
            if settings.DATA_SOURCE_TYPE == "mqtt":
                DataService._received_data_cache[device_id] = data
            print("=== 获取实时数据结束 (从数据源) ===")
            return data
        except Exception as e:
            print(f"从数据源获取实时数据失败: {e}")

        # 降级到推送缓存
        if device_id in DataService._received_data_cache:
            print(f"从缓存获取数据: {DataService._received_data_cache[device_id]}")
            print("=== 获取实时数据结束 (从缓存) ===")
            return DataService._received_data_cache[device_id]

        if settings.LOCAL_MODE:
            pressure = round(random.uniform(0.8, 1.5), 2)
            flow = round(random.uniform(8.0, 15.0), 2)
            temperature = round(random.uniform(35.0, 50.0), 2)
            data = {
                "device_id": device_id,
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "pressure": pressure,
                "flow": flow,
                "temperature": temperature,
                "status": _check_status(pressure, flow, temperature),
                "source_type": "simulate",
            }

        try:
            redis_client = get_redis_client()
            raw = redis_client.get(f"realtime:{device_id}")
            return json.loads(raw) if raw else _offline_response(device_id)
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            # 降级到内存缓存
            pressure = round(random.uniform(0.8, 1.5), 2)
            flow = round(random.uniform(8.0, 15.0), 2)
            temperature = round(random.uniform(35.0, 50.0), 2)
            data = {
                "device_id": device_id,
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                "pressure": pressure,
                "flow": flow,
                "temperature": temperature,
                "status": _check_status(pressure, flow, temperature),
                "source_type": "memory_cache",
            }
            DataService._received_data_cache[device_id] = data
            return data

    @staticmethod
    def get_history_data(device_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史数据"""
        print(f"获取历史数据: device_id={device_id}, start_time={start_time}, end_time={end_time}")
        
        # 首先尝试从数据源管理器获取数据
        try:
            manager = DataSourceManager()
            data_source = manager.get_data_source()
            history_data = data_source.get_history_data(device_id, start_time, end_time)
            
            # 处理数据格式，确保包含所有必要字段
            processed_data = []
            for data in history_data:
                pressure = data.get('pressure', 0.0)
                flow = data.get('flow', 0.0)
                temperature = data.get('temperature', 0.0)
                processed_data.append({
                    "device_id": device_id,
                    "timestamp": data.get('timestamp', datetime.now().strftime('%Y-%m-%dT%H:%M:%S')),
                    "pressure": pressure,
                    "flow": flow,
                    "temperature": temperature,
                    "status": _check_status(pressure, flow, temperature),
                    "source_type": "mqtt" if settings.DATA_SOURCE_TYPE == "mqtt" else "simulate",
                })
            
            print(f"从数据源获取历史数据成功，返回数据条数: {len(processed_data)}")
            return processed_data
        except Exception as e:
            print(f"从数据源获取历史数据失败: {e}")
            
        # 降级到原来的逻辑
        if settings.LOCAL_MODE:
            history_data = []
            total_seconds = (end_time - start_time).total_seconds()
            # 动态步长：目标约 500 个数据点，最小 5 秒
            step_seconds = max(5, int(total_seconds / 500))
            step = timedelta(seconds=step_seconds)
            current_time = start_time
            while current_time <= end_time:
                pressure = round(random.uniform(0.8, 1.5), 2)
                flow = round(random.uniform(8.0, 15.0), 2)
                temperature = round(random.uniform(35.0, 50.0), 2)
                history_data.append({
                    "device_id": device_id,
                    "timestamp": current_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    "pressure": pressure,
                    "flow": flow,
                    "temperature": temperature,
                    "status": _check_status(pressure, flow, temperature),
                    "source_type": "simulate",
                })
                current_time += step
            print(f"本地模式返回数据条数: {len(history_data)}")
            return history_data

        try:
            client = get_influxdb_client()
            query_api = client.query_api()
            query = f"""
                from(bucket: '{settings.INFLUXDB_BUCKET}')
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "pump_monitor")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
            """
            result = query_api.query(query=query, org=settings.INFLUXDB_ORG)
            history_data = []
            for table in result:
                for record in table.records:
                    history_data.append({
                        "device_id": device_id,
                        "timestamp": record["_time"].isoformat(),
                        "pressure": record.get("pressure", 0.0),
                        "flow": record.get("flow", 0.0),
                        "temperature": record.get("temperature", 0.0),
                        "status": record.get("status", "normal"),
                        "source_type": record.get("source_type", "unknown"),
                    })
            return history_data
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            # 降级到模拟数据
            print(f"降级到模拟数据: device_id={device_id}, start_time={start_time}, end_time={end_time}")
            history_data = []
            total_seconds = (end_time - start_time).total_seconds()
            # 动态步长：目标约 500 个数据点，最小 5 秒
            step_seconds = max(5, int(total_seconds / 500))
            step = timedelta(seconds=step_seconds)
            current_time = start_time
            while current_time <= end_time:
                pressure = round(random.uniform(0.8, 1.5), 2)
                flow = round(random.uniform(8.0, 15.0), 2)
                temperature = round(random.uniform(35.0, 50.0), 2)
                history_data.append({
                    "device_id": device_id,
                    "timestamp": current_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    "pressure": pressure,
                    "flow": flow,
                    "temperature": temperature,
                    "status": _check_status(pressure, flow, temperature),
                    "source_type": "memory_cache",
                })
                current_time += step
            print(f"降级模式返回数据条数: {len(history_data)}")
            return history_data

    @staticmethod
    def process_received_data(data: Dict) -> bool:
        """处理接收到的边缘网关数据，使用AI模型进行预警检测"""
        try:
            device_id = data.get("device_id")
            if not device_id:
                print("接收到的数据缺少device_id")
                return False

            pressure = data.get("pressure", 0.0)
            flow = data.get("flow", 0.0)
            temperature = data.get("temperature", 0.0)
            
            # 使用传统方法检查状态
            status = _check_status(pressure, flow, temperature)
            data["status"] = status
            
            # 使用AI模型进行预警检测
            warning_record = WarningService.process_data_and_check_warning(device_id, data)
            if warning_record:
                print(f"AI检测到预警: {device_id}, 类型: {warning_record['warning_type']}, "
                      f"置信度: {warning_record['ai_confidence']:.2%}")
                # 更新状态为预警
                data["status"] = "warning"
                data["ai_warning"] = {
                    "type": warning_record['warning_type'],
                    "confidence": warning_record['ai_confidence'],
                    "value": warning_record['warning_value'],
                    "threshold": warning_record['threshold']
                }
            
            # AI预测未来预警
            will_warn, confidence, warn_type, details = WarningService.predict_warning_with_ai(device_id, data)
            if will_warn and confidence > 0.6:
                print(f"AI预测未来预警: {device_id}, 类型: {warn_type}, "
                      f"置信度: {confidence:.2%}, 预计{details.get('time_to_warning_seconds', '未知')}秒后发生")
                data["ai_prediction"] = {
                    "will_warn": True,
                    "type": warn_type,
                    "confidence": confidence,
                    "time_to_warning": details.get('time_to_warning_seconds')
                }

            if settings.LOCAL_MODE:
                DataService._received_data_cache[device_id] = data
                print(f"数据已缓存: {device_id}, 压力: {pressure}, 流量: {flow}, 温度: {temperature}")

            try:
                redis_client = get_redis_client()
                redis_client.setex(f"realtime:{device_id}", 3600, json.dumps(data))
                print(f"数据已存储到Redis: {device_id}")
            except Exception as e:
                print(f"存储到Redis失败，降级到内存缓存: {e}")
                DataService._received_data_cache[device_id] = data
            return True

        except Exception as e:
            print(f"处理接收数据失败: {e}")
            return False
    
    @staticmethod
    def get_smart_thresholds() -> Dict:
        """获取智能阈值（历史数据的95分位值）"""
        try:
            # 获取过去24小时的历史数据
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # 收集所有设备的历史数据
            pressures = []
            flows = []
            temperatures = []
            
            # 模拟设备列表
            devices = ["device_1", "device_2", "device_3"]
            
            for device_id in devices:
                history_data = DataService.get_history_data(device_id, start_time, end_time)
                for data in history_data:
                    pressures.append(data.get("pressure", 0.0))
                    flows.append(data.get("flow", 0.0))
                    temperatures.append(data.get("temperature", 0.0))
            
            # 计算95分位值
            if pressures and flows and temperatures:
                pressure_threshold = round(float(np.percentile(pressures, 95)), 2)
                flow_threshold = round(float(np.percentile(flows, 95)), 2)
                temperature_threshold = round(float(np.percentile(temperatures, 95)), 2)
            else:
                # 如果没有历史数据，使用默认值
                pressure_threshold = 1.8
                flow_threshold = 12.5
                temperature_threshold = 45.0
            
            return {
                "pressure_threshold": pressure_threshold,
                "flow_threshold": flow_threshold,
                "temperature_threshold": temperature_threshold
            }
        except Exception as e:
            print(f"计算智能阈值失败: {e}")
            # 降级到默认值
            return {
                "pressure_threshold": 1.8,
                "flow_threshold": 12.5,
                "temperature_threshold": 45.0
            }
    
    @staticmethod
    def get_ai_stats(device_id: str) -> Dict:
        """获取设备的AI统计信息"""
        return WarningService.get_ai_stats(device_id)
