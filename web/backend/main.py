# -*- coding: utf-8 -*-
"""
Web Digital Twin Backend
FastAPI应用入口
"""
import sys
import os
import warnings

# 过滤 snap7 的 pkg_resources 弃用警告（第三方库内部问题）
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 添加src目录到路径（复用现有模块）
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from web.backend.websocket.manager import websocket_manager
from web.backend.api import auth, system, device, fan, env, plc, motion, sensor, sync
from web.backend.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动Web数字孪生后端服务...")
    # 启动时执行
    yield
    # 关闭时执行
    logger.info("关闭Web数字孪生后端服务...")


# 创建FastAPI应用
app = FastAPI(
    title="Web Digital Twin API",
    description="微小型无人机智能风场测试评估系统 - Web数字孪生接口",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])
app.include_router(device.router, prefix="/api/device", tags=["设备"])
app.include_router(fan.router, prefix="/api/fan", tags=["风扇"])
app.include_router(env.router, prefix="/api/env", tags=["环境"])
app.include_router(plc.router, prefix="/api/plc", tags=["PLC"])
app.include_router(motion.router, prefix="/api/motion", tags=["动捕"])
app.include_router(sensor.router, prefix="/api/sensor", tags=["传感器"])
app.include_router(sync.router, prefix="/api", tags=["同步"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Web Digital Twin API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            await websocket_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        websocket_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动服务器: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")

    uvicorn.run(
        "web.backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
