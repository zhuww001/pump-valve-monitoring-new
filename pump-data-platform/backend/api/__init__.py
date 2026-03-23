from fastapi import APIRouter
from api.device import device_router
from api.data import data_router
from api.warning import warning_router
from api.data_source import data_source_router
from api.websocket import websocket_router
from api.auth import auth_router

# 创建API路由
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(device_router, prefix="/device", tags=["device"])
api_router.include_router(data_router, prefix="/data", tags=["data"])
api_router.include_router(warning_router, prefix="/warning", tags=["warning"])
api_router.include_router(data_source_router, prefix="/data-source", tags=["data-source"])
api_router.include_router(websocket_router, prefix="/websocket", tags=["websocket"])
