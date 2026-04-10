# -*- coding: utf-8 -*-
"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # MongoDB配置
    MONGODB_URI: str = "mongodb://localhost:27017/"
    MONGODB_DATABASE: str = "wind_field_test"

    # PLC配置
    PLC_IP: str = "192.168.1.100"
    PLC_RACK: int = 0
    PLC_SLOT: int = 1

    # 动捕配置
    MOTION_IP: str = "192.168.1.50"

    # 风扇控制配置
    FAN_UDP_START_IP: str = "192.168.1.101"
    FAN_UDP_END_IP: str = "192.168.1.200"
    FAN_UDP_PORT: int = 5001

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
