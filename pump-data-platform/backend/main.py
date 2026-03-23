from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from api import api_router
from core.config import settings
from core.data_process import DataCollector
from core.db.postgres import init_postgres_pool
from core.db.influxdb import init_influxdb_client
from core.db.redis import init_redis_client
import asyncio

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="泵阀管道堵塞预警系统统一数据后台"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api")

# 启动数据采集任务
async def start_data_collection():
    """启动数据采集任务"""
    collector = DataCollector()
    while True:
        collector.collect()
        await asyncio.sleep(settings.COLLECTION_INTERVAL)

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 初始化数据库连接
    if not settings.LOCAL_MODE:
        print("初始化数据库连接...")
        init_postgres_pool()
        init_influxdb_client()
        init_redis_client()
        print("数据库连接初始化完成")
    
    # 启动数据采集任务
    asyncio.create_task(start_data_collection())

# 根路径
@app.get("/")
def read_root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )
