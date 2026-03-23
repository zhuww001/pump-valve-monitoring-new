import json
from datetime import datetime
from typing import Dict
from ..db import get_influxdb_client, get_postgres_connection, get_redis_client, release_postgres_connection
from ..config import settings


class DataIngestion:
    """统一入库"""
    
    @staticmethod
    def ingest(data: Dict):
        """数据入库
        
        Args:
            data: 标准化后的数据
        """
        # 本地运行模式下跳过数据库操作
        if not settings.LOCAL_MODE:
            # 写入时序数据库
            DataIngestion._write_to_influxdb(data)
            
            # 写入缓存
            DataIngestion._write_to_redis(data)
            
            # 检查是否需要写入预警记录
            if data.get("status") == "warning":
                DataIngestion._write_warning_record(data)
    
    @staticmethod
    def _write_to_influxdb(data: Dict):
        """写入InfluxDB"""
        try:
            client = get_influxdb_client()
            write_api = client.write_api()
            
            # 构建点数据
            point = {
                "measurement": "pump_monitor",
                "tags": {
                    "device_id": data.get("device_id"),
                    "status": data.get("status"),
                    "source_type": data.get("source_type")
                },
                "time": data.get("timestamp"),
                "fields": {
                    "pressure": data.get("pressure"),
                    "flow": data.get("flow"),
                    "temperature": data.get("temperature")
                }
            }
            
            # 写入数据
            write_api.write(
                bucket=settings.INFLUXDB_BUCKET,
                org=settings.INFLUXDB_ORG,
                record=point
            )
        except Exception as e:
            print(f"写入InfluxDB失败: {e}")
    
    @staticmethod
    def _write_to_redis(data: Dict):
        """写入Redis缓存"""
        try:
            redis_client = get_redis_client()
            device_id = data.get("device_id")
            key = f"realtime:{device_id}"
            
            # 写入缓存，设置过期时间3600秒
            redis_client.setex(
                key,
                3600,
                json.dumps(data)
            )
        except Exception as e:
            print(f"写入Redis失败: {e}")
    
    @staticmethod
    def _write_warning_record(data: Dict):
        """写入预警记录"""
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            # 插入预警记录
            query = """
                INSERT INTO warning_record (
                    device_id, warning_type, warning_value, threshold, status, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            # 确定预警类型和值
            warning_type = ""
            warning_value = 0.0
            threshold = 0.0
            
            pressure = data.get("pressure")
            flow = data.get("flow")
            temperature = data.get("temperature")
            
            if pressure > settings.PRESSURE_THRESHOLD:
                warning_type = "pressure"
                warning_value = pressure
                threshold = settings.PRESSURE_THRESHOLD
            elif flow < settings.FLOW_THRESHOLD:
                warning_type = "flow"
                warning_value = flow
                threshold = settings.FLOW_THRESHOLD
            elif temperature > settings.TEMPERATURE_THRESHOLD:
                warning_type = "temperature"
                warning_value = temperature
                threshold = settings.TEMPERATURE_THRESHOLD
            
            # 执行插入
            current_time = datetime.now()
            cursor.execute(
                query,
                (
                    data.get("device_id"),
                    warning_type,
                    warning_value,
                    threshold,
                    "unprocessed",
                    current_time,
                    current_time
                )
            )
            
            conn.commit()
            cursor.close()
            release_postgres_connection(conn)
        except Exception as e:
            print(f"写入预警记录失败: {e}")
            if 'conn' in locals():
                release_postgres_connection(conn)
