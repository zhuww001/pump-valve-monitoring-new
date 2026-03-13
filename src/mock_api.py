from fastapi import FastAPI, Query
import uvicorn
import random
from datetime import datetime, timedelta
import json

app = FastAPI()

# 全局状态 - 支持多设备
class DeviceState:
    def __init__(self, device_id):
        self.device_id = device_id
        self.mode = "normal"  # normal, blockage
        self.start_time = datetime.now()
        
        # 根据设备ID设置不同的基准值
        if device_id == "device_1":
            self.pressure_base = 0.8
            self.flow_base = 12.5
        elif device_id == "device_2":
            self.pressure_base = 0.75
            self.flow_base = 13.0
        elif device_id == "device_3":
            self.pressure_base = 0.85
            self.flow_base = 12.0
        else:
            self.pressure_base = 0.8
            self.flow_base = 12.5
            
        self.valve_open = 100
        self.temperature = 45.2
        
        # 堵塞工况参数
        self.blockage_start_time = self.start_time + timedelta(minutes=5)
        self.pressure_increase = 0.15  # 每5分钟增加量
        self.flow_decrease = 3.0  # 每5分钟减少量

# 设备状态字典
device_states = {}

@app.get("/api/pump-data")
async def get_pump_data(device_id: str = Query("device_1", description="设备ID")):
    # 确保设备状态存在
    if device_id not in device_states:
        device_states[device_id] = DeviceState(device_id)
    
    state = device_states[device_id]
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 计算运行时间（分钟）
    run_time = (current_time - state.start_time).total_seconds() / 60
    
    if state.mode == "normal":
        # 正常工况：压力和流量小幅波动
        pressure = state.pressure_base + random.uniform(-0.02, 0.02)
        flow = state.flow_base + random.uniform(-0.3, 0.3)
    else:
        # 堵塞工况：压力逐渐上升，流量逐渐下降
        if current_time >= state.blockage_start_time:
            # 计算堵塞时间（分钟）
            blockage_time = (current_time - state.blockage_start_time).total_seconds() / 60
            # 每5分钟的变化量
            pressure_increase = (blockage_time / 5) * state.pressure_increase
            flow_decrease = (blockage_time / 5) * state.flow_decrease
            
            pressure = state.pressure_base + pressure_increase + random.uniform(-0.01, 0.01)
            flow = state.flow_base - flow_decrease + random.uniform(-0.1, 0.1)
        else:
            # 堵塞前的正常状态
            pressure = state.pressure_base + random.uniform(-0.02, 0.02)
            flow = state.flow_base + random.uniform(-0.3, 0.3)
    
    # 确保数值合理
    pressure = max(0, round(pressure, 2))
    flow = max(0, round(flow, 1))
    
    data = {
        "code": 200,
        "msg": "success",
        "data": {
            "device_id": device_id,
            "timestamp": timestamp,
            "pressure": pressure,
            "flow": flow,
            "valve_open": state.valve_open,
            "temperature": state.temperature
        }
    }
    
    return data

@app.post("/api/set-mode")
async def set_mode(mode: str = Query(..., description="模式: normal 或 blockage"), device_id: str = Query("device_1", description="设备ID")):
    if mode not in ["normal", "blockage"]:
        return {"code": 400, "msg": "无效的模式"}
    
    # 确保设备状态存在
    if device_id not in device_states:
        device_states[device_id] = DeviceState(device_id)
    
    state = device_states[device_id]
    state.mode = mode
    if mode == "blockage":
        # 重置堵塞开始时间，立即开始堵塞工况
        state.blockage_start_time = datetime.now() - timedelta(minutes=1)
    
    return {"code": 200, "msg": f"设备 {device_id} 模式已设置为: {mode}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
