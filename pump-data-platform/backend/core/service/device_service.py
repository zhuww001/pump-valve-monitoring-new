from typing import List, Dict
from ..db import get_postgres_connection
from ..config import settings
from ..data_source.manager import DataSourceManager


# 本地模式使用的静态设备列表
_MOCK_DEVICES: List[Dict] = [
    {"id": 1, "device_id": "device_1", "name": "泵 A", "location": "一号车间", "负责人": "", "联系方式": "",
     "pressure_threshold": 2.0, "flow_threshold": 5.0, "temperature_threshold": 80.0, "status": "normal"},
    {"id": 2, "device_id": "device_2", "name": "泵 B", "location": "二号车间", "负责人": "", "联系方式": "",
     "pressure_threshold": 2.0, "flow_threshold": 5.0, "temperature_threshold": 80.0, "status": "normal"},
    {"id": 3, "device_id": "device_3", "name": "泵 C", "location": "三号车间", "负责人": "", "联系方式": "",
     "pressure_threshold": 2.0, "flow_threshold": 5.0, "temperature_threshold": 80.0, "status": "normal"},
    {"id": 4, "device_id": "B0320001", "name": "泵 D", "location": "四号车间", "负责人": "", "联系方式": "",
     "pressure_threshold": 2.0, "flow_threshold": 5.0, "temperature_threshold": 80.0, "status": "normal"},
]


def _row_to_device(row) -> Dict:
    return {
        "id": row[0],
        "device_id": row[1],
        "name": row[2],
        "location": row[3],
        "pressure_threshold": row[4],
        "flow_threshold": row[5],
        "temperature_threshold": row[6],
        "status": row[7],
        "created_at": row[8].isoformat(),
        "updated_at": row[9].isoformat(),
        "负责人": row[10] if len(row) > 10 else "",
        "联系方式": row[11] if len(row) > 11 else "",
    }


class DeviceService:
    """设备管理服务"""

    @staticmethod
    def get_device_list() -> List[Dict]:
        """获取设备列表"""
        # 首先尝试从数据源管理器获取设备列表
        try:
            manager = DataSourceManager()
            data_source = manager.get_data_source()
            print(f"当前数据源类型: {settings.DATA_SOURCE_TYPE}")
            data_source_devices = data_source.get_device_list()
            print(f"从数据源获取的设备列表: {data_source_devices}")
            
            # 处理设备列表格式
            if data_source_devices:
                processed_devices = []
                for device in data_source_devices:
                    device_id = device.get('device_id')
                    if device_id:
                        # 为每个设备添加阈值信息
                        device_info = DeviceService.get_device_by_id(device_id)
                        processed_device = {
                            "id": device_info.get("id", len(processed_devices) + 1),
                            "device_id": device_id,
                            "name": device.get('name', f"设备 {device_id}"),
                            "location": device_info.get("location", "未知位置"),
                            "负责人": device_info.get("负责人", ""),
                            "联系方式": device_info.get("联系方式", ""),
                            "pressure_threshold": device_info.get("pressure_threshold", 2.0),
                            "flow_threshold": device_info.get("flow_threshold", 5.0),
                            "temperature_threshold": device_info.get("temperature_threshold", 80.0),
                            "status": device.get('status', "normal")
                        }
                        processed_devices.append(processed_device)
                print(f"处理后的设备列表: {processed_devices}")
                if processed_devices:
                    return processed_devices
        except Exception as e:
            print(f"从数据源获取设备列表失败: {e}")
            import traceback
            traceback.print_exc()
            
        # 降级到原来的逻辑
        if settings.LOCAL_MODE:
            print("降级到本地模式设备列表")
            return _MOCK_DEVICES

        conn = None
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM device")
            devices = [_row_to_device(row) for row in cursor.fetchall()]
            cursor.close()
            return devices
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return _MOCK_DEVICES
        finally:
            from core.db.postgres import release_postgres_connection
            if conn:
                release_postgres_connection(conn)

    @staticmethod
    def update_device_threshold(device_id: str, thresholds: Dict) -> bool:
        """更新设备阈值"""
        if settings.LOCAL_MODE:
            return True

        conn = None
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE device SET
                    pressure_threshold = %s,
                    flow_threshold = %s,
                    temperature_threshold = %s,
                    updated_at = NOW()
                WHERE device_id = %s
                """,
                (
                    thresholds.get("pressure_threshold"),
                    thresholds.get("flow_threshold"),
                    thresholds.get("temperature_threshold"),
                    device_id,
                ),
            )
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"更新设备阈值失败: {e}")
            return False
        finally:
            from core.db.postgres import release_postgres_connection
            if conn:
                release_postgres_connection(conn)

    @staticmethod
    def get_device_by_id(device_id: str) -> Dict:
        """根据设备ID获取设备信息"""
        if settings.LOCAL_MODE:
            device = next((d for d in _MOCK_DEVICES if d["device_id"] == device_id), None)
            if device:
                return device
            else:
                # 为MQTT设备返回默认设备信息
                return {
                    "id": 999,  # 临时ID
                    "device_id": device_id,
                    "name": f"设备 {device_id}",
                    "location": "未知位置",
                    "负责人": "",
                    "联系方式": "",
                    "pressure_threshold": 2.0,
                    "flow_threshold": 5.0,
                    "temperature_threshold": 80.0,
                    "status": "online"
                }

        conn = None
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM device WHERE device_id = %s", (device_id,))
            row = cursor.fetchone()
            cursor.close()
            if row:
                return _row_to_device(row)
            else:
                # 为MQTT设备返回默认设备信息
                return {
                    "id": 999,  # 临时ID
                    "device_id": device_id,
                    "name": f"设备 {device_id}",
                    "location": "未知位置",
                    "负责人": "",
                    "联系方式": "",
                    "pressure_threshold": 2.0,
                    "flow_threshold": 5.0,
                    "temperature_threshold": 80.0,
                    "status": "online"
                }
        except Exception as e:
            print(f"获取设备信息失败: {e}")
            # 为MQTT设备返回默认设备信息
            return {
                "id": 999,  # 临时ID
                "device_id": device_id,
                "name": f"设备 {device_id}",
                "location": "未知位置",
                "负责人": "",
                "联系方式": "",
                "pressure_threshold": 2.0,
                "flow_threshold": 5.0,
                "temperature_threshold": 80.0,
                "status": "online"
            }
        finally:
            from core.db.postgres import release_postgres_connection
            if conn:
                release_postgres_connection(conn)

    @staticmethod
    def update_device_info(device_id: str, device_info: Dict) -> bool:
        """更新设备基本信息"""
        if settings.LOCAL_MODE:
            # 本地模式下更新静态设备列表
            device = next((d for d in _MOCK_DEVICES if d["device_id"] == device_id), None)
            if device:
                device.update(device_info)
                # 确保本地模式的设备也有负责人和联系方式字段
                if not "负责人" in device:
                    device["负责人"] = device_info.get("负责人", "")
                if not "联系方式" in device:
                    device["联系方式"] = device_info.get("联系方式", "")
                return True
            else:
                # 如果设备不存在，添加新设备
                new_device = {
                    "id": len(_MOCK_DEVICES) + 1,
                    "device_id": device_id,
                    "name": device_info.get("name", f"设备 {device_id}"),
                    "location": device_info.get("location", "未知位置"),
                    "负责人": device_info.get("负责人", ""),
                    "联系方式": device_info.get("联系方式", ""),
                    "pressure_threshold": 2.0,
                    "flow_threshold": 5.0,
                    "temperature_threshold": 80.0,
                    "status": "normal"
                }
                _MOCK_DEVICES.append(new_device)
                return True

        conn = None
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE device SET
                    name = %s,
                    location = %s,
                    负责人 = %s,
                    联系方式 = %s,
                    updated_at = NOW()
                WHERE device_id = %s
                """,
                (
                    device_info.get("name"),
                    device_info.get("location"),
                    device_info.get("负责人"),
                    device_info.get("联系方式"),
                    device_id,
                ),
            )
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"更新设备信息失败: {e}")
            return False
        finally:
            from core.db.postgres import release_postgres_connection
            if conn:
                release_postgres_connection(conn)
