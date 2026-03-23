import random
from datetime import datetime, timedelta
from typing import List, Dict
from .base import BaseDataSource

# 历史数据最多返回条数（5秒/条，约2小时）
_MAX_HISTORY_RECORDS = 1440


class SimulateDataSource(BaseDataSource):
    """模拟数据源"""

    def __init__(self):
        self.devices = [
            {"id": "device_1", "name": "泵 A", "location": "一号车间"},
            {"id": "device_2", "name": "泵 B", "location": "二号车间"},
            {"id": "device_3", "name": "泵 C", "location": "三号车间"},
            {"id": "B0320001", "name": "泵 D", "location": "四号车间"},
        ]
        self.device_status = {
            "device_1": {"pressure": 1.0, "flow": 10.0, "temperature": 40.0},
            "device_2": {"pressure": 1.2, "flow": 12.0, "temperature": 42.0},
            "device_3": {"pressure": 0.9, "flow":  9.0, "temperature": 38.0},
            "B0320001": {"pressure": 2.3, "flow": 11.0, "temperature": 45.0},  # 压力超过阈值 2.0
        }
        self.thresholds = {"pressure": 2.0, "flow": 5.0, "temperature": 80.0}

    def _determine_status(self, pressure: float, flow: float, temperature: float) -> str:
        if (pressure > self.thresholds["pressure"]
                or flow < self.thresholds["flow"]
                or temperature > self.thresholds["temperature"]):
            return "warning"
        return "normal"

    def get_realtime_data(self, device_id: str) -> Dict:
        """获取实时数据"""
        if device_id not in self.device_status:
            return {
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "pressure": 0.0, "flow": 0.0, "temperature": 0.0,
                "status": "offline", "source_type": "simulate",
            }

        s = self.device_status[device_id]
        s["pressure"]     = max(0, s["pressure"]     + random.uniform(-0.1, 0.1))
        s["flow"]         = max(0, s["flow"]         + random.uniform(-0.5, 0.5))
        s["temperature"]  = max(0, s["temperature"]  + random.uniform(-0.5, 0.5))

        pressure, flow, temperature = s["pressure"], s["flow"], s["temperature"]
        return {
            "device_id": device_id,
            "timestamp": datetime.now().isoformat(),
            "pressure": round(pressure, 2),
            "flow": round(flow, 2),
            "temperature": round(temperature, 2),
            "status": self._determine_status(pressure, flow, temperature),
            "source_type": "simulate",
        }

    def get_history_data(self, device_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """获取历史数据"""
        history_data = []
        current_time = start_time
        step = timedelta(seconds=5)
        count = 0
        while current_time <= end_time and count < _MAX_HISTORY_RECORDS:
            pressure    = round(random.uniform(0.8, 1.5),  2)
            flow        = round(random.uniform(8.0, 15.0), 2)
            temperature = round(random.uniform(35.0, 50.0), 2)
            history_data.append({
                "device_id": device_id,
                "timestamp": current_time.isoformat(),
                "pressure": pressure,
                "flow": flow,
                "temperature": temperature,
                "status": self._determine_status(pressure, flow, temperature),
                "source_type": "simulate",
            })
            current_time += step
            count += 1
        return history_data

    def get_device_list(self) -> List[Dict]:
        """获取设备列表"""
        return self.devices
