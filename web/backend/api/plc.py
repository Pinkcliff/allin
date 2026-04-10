# -*- coding: utf-8 -*-
"""
PLC监控API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter()


class PLCStatusResponse(BaseModel):
    """PLC状态响应"""
    connected: bool
    ip_address: str
    last_update: str


class EncoderDataResponse(BaseModel):
    """编码器数据响应"""
    encoder_id: int
    position: float
    velocity: float
    timestamp: str


class PointDataResponse(BaseModel):
    """点表数据响应"""
    point_name: str
    value: float
    unit: str
    timestamp: str


@router.get("/status", response_model=PLCStatusResponse)
async def get_plc_status():
    """获取PLC连接状态"""
    # TODO: 实际检查PLC连接状态
    return PLCStatusResponse(
        connected=True,
        ip_address="192.168.1.100",
        last_update=datetime.now().isoformat()
    )


@router.get("/encoder")
async def get_encoder_data(encoder_id: Optional[int] = None):
    """
    获取编码器数据

    - encoder_id: 编码器ID，不传则返回所有
    """
    # TODO: 从PLC实际读取编码器数据
    import random

    if encoder_id is not None:
        return {
            "encoder_id": encoder_id,
            "position": random.uniform(0, 360),
            "velocity": random.uniform(-100, 100),
            "timestamp": datetime.now().isoformat()
        }

    # 返回多个编码器数据
    encoders = []
    for i in range(1, 9):
        encoders.append({
            "encoder_id": i,
            "position": random.uniform(0, 360),
            "velocity": random.uniform(-100, 100),
            "timestamp": datetime.now().isoformat()
        })

    return {"encoders": encoders}


@router.get("/point")
async def get_point_data(point_name: Optional[str] = None):
    """
    获取点表数据

    - point_name: 点表名称，不传则返回所有
    """
    # TODO: 从PLC实际读取点表数据
    import random

    if point_name is not None:
        return {
            "point_name": point_name,
            "value": random.uniform(0, 100),
            "unit": "%",
            "timestamp": datetime.now().isoformat()
        }

    # 返回常用点表数据
    points = {
        "主电机速度": {"value": random.uniform(0, 1500), "unit": "RPM"},
        "主电机电流": {"value": random.uniform(0, 10), "unit": "A"},
        "油压": {"value": random.uniform(0, 10), "unit": "MPa"},
        "油温": {"value": random.uniform(20, 80), "unit": "°C"},
        "冷却水温": {"value": random.uniform(20, 60), "unit": "°C"},
    }

    result = []
    for name, data in points.items():
        result.append({
            "point_name": name,
            "value": data["value"],
            "unit": data["unit"],
            "timestamp": datetime.now().isoformat()
        })

    return {"points": result}


@router.get("/history/encoder")
async def get_encoder_history(
    encoder_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100
):
    """
    获取编码器历史数据

    - encoder_id: 编码器ID
    - start_time: 开始时间（ISO格式）
    - end_time: 结束时间（ISO格式）
    - limit: 返回条数
    """
    # TODO: 从数据库获取历史数据
    import random
    from datetime import timedelta

    data = []
    base_time = datetime.now()
    for i in range(limit):
        timestamp = base_time - timedelta(seconds=limit - i)
        data.append({
            "timestamp": timestamp.isoformat(),
            "position": random.uniform(0, 360),
            "velocity": random.uniform(-100, 100)
        })

    return {
        "encoder_id": encoder_id,
        "data": data,
        "count": len(data)
    }
