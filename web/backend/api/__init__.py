# -*- coding: utf-8 -*-
"""
API路由模块
"""
from fastapi import APIRouter

# 导入各个路由模块
from . import auth, system, device, fan, env, plc, motion, sensor

__all__ = [
    "auth",
    "system",
    "device",
    "fan",
    "env",
    "plc",
    "motion",
    "sensor"
]
