from fastapi import APIRouter, HTTPException
from typing import List, Dict
from core.service import WarningService

warning_router = APIRouter()


@warning_router.get("/list", response_model=Dict)
def get_warning_list(page: int = 1, page_size: int = 10, device_id: str = None):
    """获取预警列表，支持按设备ID筛选"""
    warnings = WarningService.get_warning_list(page, page_size, device_id)
    total = WarningService.get_warning_count(device_id)
    return {"items": warnings, "total": total}


@warning_router.put("/status/{warning_id}")
def update_warning_status(warning_id: int, status: Dict):
    """更新预警状态"""
    success = WarningService.update_warning_status(warning_id, status.get("status"))
    if not success:
        raise HTTPException(status_code=500, detail="更新预警状态失败")
    return {"message": "更新成功"}
