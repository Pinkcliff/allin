# -*- coding: utf-8 -*-
"""
风扇控制API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局风扇数据存储（用于从桌面端同步）
_fan_data_store = {
    "fan_array": [[0 for _ in range(40)] for _ in range(40)],
    "last_update": None,
    "last_timestamp": 0  # 【新增】记录最新的时间戳
}


class FanStatusResponse(BaseModel):
    """风扇状态响应"""
    total_fans: int
    online_fans: int
    active_fans: int
    fan_array: List[List[int]]  # 40x40 array, 0=off, 1=on


class FanPowerRequest(BaseModel):
    """风扇电源控制"""
    power_on: bool


class FanAreaRequest(BaseModel):
    """风扇区域控制"""
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    rpm: int


class FanSingleRequest(BaseModel):
    """单风扇设置"""
    x: int
    y: int
    rpm: int


class FanTemplateRequest(BaseModel):
    """风扇模板"""
    name: str
    description: Optional[str] = None
    data: List[List[int]]


@router.get("/status")
async def get_fan_status():
    """
    获取风扇阵列状态

    返回40x40风扇阵列的状态（PWM值0-1000）
    """
    # 从存储中获取数据（从桌面端同步的数据）
    fan_array = _fan_data_store["fan_array"]

    # 计算统计数据
    total_fans = 40 * 40  # 1600
    online_fans = total_fans  # 假设所有风扇都在线
    active_fans = sum(1 for row in fan_array for cell in row if cell > 0)  # PWM大于0的风扇数量

    return {
        "total_fans": total_fans,
        "online_fans": online_fans,
        "active_fans": active_fans,
        "fan_array": fan_array
    }


@router.post("/power")
async def set_fan_power(request: FanPowerRequest):
    """
    全部风扇开关控制
    """
    # TODO: 通过UDP发送控制命令到硬件
    return {
        "success": True,
        "power_on": request.power_on,
        "message": f"所有风扇已{'开启' if request.power_on else '关闭'}"
    }


@router.post("/sync")
async def sync_fan_array(data: Dict[str, Any]):
    """
    接收桌面端风扇阵列数据同步

    Args:
        data: 包含fan_array和timestamp的字典
    """
    try:
        from web.backend.websocket.manager import websocket_manager

        # 更新本地存储
        if "fan_array" in data:
            fan_array = data["fan_array"]
            timestamp = data.get("timestamp", 0)

            # 【新增】时间戳检查：只处理比当前更新的数据
            if timestamp <= _fan_data_store["last_timestamp"]:
                logger.debug(f"忽略旧数据，当前: {_fan_data_store['last_timestamp']}, 收到: {timestamp}")
                return {"success": True, "message": "忽略旧数据"}

            _fan_data_store["fan_array"] = fan_array
            _fan_data_store["last_update"] = timestamp
            _fan_data_store["last_timestamp"] = timestamp

            # 计算统计数据
            active_count = sum(1 for row in fan_array for cell in row if cell > 0)

            # 通过WebSocket推送到所有Web客户端
            await websocket_manager.broadcast("fan_update", {
                "fan_array": fan_array,
                "total_fans": 1600,
                "active_fans": active_count,
                "timestamp": timestamp
            })

            logger.info(f"风扇阵列已同步: {active_count} 个风扇运行中")
            return {"success": True, "message": "风扇阵列同步成功"}
        else:
            return {"success": False, "message": "无效的数据格式"}
    except Exception as e:
        logger.error(f"风扇阵列同步失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/area")
async def set_fan_area(request: FanAreaRequest):
    """
    区域风扇控制

    - start_x, start_y: 区域起始坐标 (0-39)
    - end_x, end_y: 区域结束坐标 (0-39)
    - rpm: 转速 (0-15000)
    """
    # TODO: 通过UDP发送区域控制命令
    return {
        "success": True,
        "area": f"({request.start_x},{request.start_y}) to ({request.end_x},{request.end_y})",
        "rpm": request.rpm,
        "message": "区域控制已发送"
    }


@router.put("/single")
async def set_single_fan(request: FanSingleRequest):
    """
    单风扇设置

    - x, y: 风扇坐标 (0-39)
    - rpm: 转速 (0-15000)
    """
    # TODO: 通过UDP发送单风扇控制命令
    return {
        "success": True,
        "position": f"({request.x},{request.y})",
        "rpm": request.rpm,
        "message": "单风扇设置已发送"
    }


@router.get("/templates")
async def get_fan_templates():
    """获取风扇模板列表"""
    return {
        "templates": [
            {"id": 1, "name": "均匀分布", "description": "所有风扇相同转速"},
            {"id": 2, "name": "中心聚焦", "description": "中心区域高转速"},
            {"id": 3, "name": "梯度分布", "description": "从左到右递增"},
        ]
    }


@router.post("/template")
async def save_fan_template(request: FanTemplateRequest):
    """保存风扇模板"""
    # TODO: 保存到数据库
    return {
        "success": True,
        "id": 4,
        "message": "模板已保存"
    }
