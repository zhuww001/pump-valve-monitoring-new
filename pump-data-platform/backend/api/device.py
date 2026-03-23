from fastapi import APIRouter, HTTPException
from typing import List, Dict
from core.service import DeviceService

device_router = APIRouter()


@device_router.get("/list", response_model=Dict)
def get_device_list(
    page: int = 1,
    page_size: int = 3
):
    """获取设备列表"""
    try:
        devices = DeviceService.get_device_list()
        total = len(devices)
        start = (page - 1) * page_size
        end = start + page_size
        paged_devices = devices[start:end]
        return {
            "total": total,
            "devices": paged_devices,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        print(f"获取设备列表失败: {e}")
        # 返回默认数据，确保前端不会因为数据格式错误而不显示
        return {
            "total": 0,
            "devices": [],
            "page": page,
            "page_size": page_size
        }


@device_router.put("/threshold/{device_id}")
def update_device_threshold(device_id: str, thresholds: Dict):
    """更新设备阈值"""
    success = DeviceService.update_device_threshold(device_id, thresholds)
    if not success:
        raise HTTPException(status_code=500, detail="更新设备阈值失败")
    return {"message": "更新成功"}


@device_router.get("/{device_id}", response_model=Dict)
def get_device(device_id: str):
    """根据设备ID获取设备信息"""
    device = DeviceService.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@device_router.put("/{device_id}")
def update_device(device_id: str, device_info: Dict):
    """更新设备基本信息"""
    success = DeviceService.update_device_info(device_id, device_info)
    if not success:
        raise HTTPException(status_code=500, detail="更新设备信息失败")
    return {"message": "更新成功"}
