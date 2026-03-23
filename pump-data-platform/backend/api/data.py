from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from core.service import DataService, WarningService
import json

data_router = APIRouter()


class ReceiveDataRequest(BaseModel):
    """接收边缘网关数据请求模型"""
    device_id: str
    timestamp: str
    pressure: float
    flow: float
    temperature: float
    status: str = "normal"
    source_type: str = "edge_gateway"
    gateway_id: Optional[str] = None


@data_router.get("/realtime/{device_id}", response_model=Dict)
def get_realtime_data(device_id: str):
    """获取实时数据"""
    return DataService.get_realtime_data(device_id)


@data_router.get("/history/{device_id}", response_model=List[Dict])
def get_history_data(
    device_id: str,
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间")
):
    """获取历史数据"""
    return DataService.get_history_data(device_id, start_time, end_time)


@data_router.post("/receive", response_model=Dict)
def receive_data(data: ReceiveDataRequest):
    """
    接收边缘网关上报的传感器数据
    
    - **device_id**: 设备ID
    - **timestamp**: 数据时间戳
    - **pressure**: 压力值 (MPa)
    - **flow**: 流量值 (m³/h)
    - **temperature**: 温度值 (°C)
    - **status**: 设备状态
    - **source_type**: 数据源类型
    - **gateway_id**: 网关ID（可选）
    """
    try:
        result = DataService.process_received_data(data.model_dump())
        if not result:
            raise HTTPException(status_code=500, detail="数据处理失败")
        return {
            "success": True,
            "message": "数据接收成功",
            "device_id": data.device_id,
            "timestamp": data.timestamp,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据处理失败: {str(e)}")


@data_router.post("/receive/batch", response_model=Dict)
def receive_batch_data(data_list: List[ReceiveDataRequest]):
    """
    批量接收边缘网关上报的传感器数据
    
    - **data_list**: 传感器数据列表
    """
    try:
        success_count = 0
        failed_count = 0
        
        for data in data_list:
            try:
                DataService.process_received_data(data.model_dump())
                success_count += 1
            except Exception as e:
                print(f"处理数据失败: {data.device_id}, 错误: {e}")
                failed_count += 1
        
        return {
            "success": True,
            "message": f"批量数据处理完成，成功: {success_count}, 失败: {failed_count}",
            "success_count": success_count,
            "failed_count": failed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量数据处理失败: {str(e)}")


@data_router.get("/ai/stats/{device_id}", response_model=Dict)
def get_ai_stats(device_id: str):
    """
    获取设备的AI模型统计信息
    
    - **device_id**: 设备ID
    """
    try:
        stats = DataService.get_ai_stats(device_id)
        return {
            "success": True,
            "device_id": device_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI统计信息失败: {str(e)}")


@data_router.get("/ai/predict/{device_id}", response_model=Dict)
def predict_warning(device_id: str):
    """
    使用AI模型预测设备未来预警
    
    - **device_id**: 设备ID
    """
    try:
        # 获取当前数据
        current_data = DataService.get_realtime_data(device_id)
        
        # 使用AI预测
        will_warn, confidence, warn_type, details = WarningService.predict_warning_with_ai(
            device_id, current_data
        )
        
        return {
            "success": True,
            "device_id": device_id,
            "prediction": {
                "will_warn": will_warn,
                "confidence": confidence,
                "warning_type": warn_type,
                "details": details
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI预测失败: {str(e)}")


@data_router.get("/smart-thresholds", response_model=Dict)
def get_smart_thresholds():
    """
    获取智能阈值（历史数据的95分位值）
    """
    try:
        thresholds = DataService.get_smart_thresholds()
        return {
            "success": True,
            "thresholds": thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能阈值失败: {str(e)}")
