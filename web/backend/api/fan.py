# -*- coding: utf-8 -*-
"""
风扇控制API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


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


@router.get("/status", response_model=FanStatusResponse)
async def get_fan_status():
    """
    获取风扇阵列状态

    返回40x40风扇阵列的状态
    """
    # TODO: 从实际硬件获取状态
    import random
    fan_array = [[random.randint(0, 1) for _ in range(40)] for _ in range(40)]

    return FanStatusResponse(
        total_fans=1600,
        online_fans=1600,
        active_fans=sum(sum(row) for row in fan_array),
        fan_array=fan_array
    )


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
