# -*- coding: utf-8 -*-
"""
Redis数据库接口模块
用于传感器数据的存储和检索
"""
import json
import time
from datetime import datetime
from typing import List, Dict, Optional


class RedisDatabase:
    """Redis数据库接口"""

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        初始化Redis连接

        Args:
            host: Redis服务器地址
            port: Redis端口
            db: Redis数据库编号
            password: Redis密码
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None
        self._connected = False

    def connect(self):
        """连接到Redis服务器"""
        try:
            import redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # 测试连接
            self._client.ping()
            self._connected = True
            return True
        except Exception as e:
            print(f"Redis连接失败: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """断开Redis连接"""
        if self._client:
            self._client.close()
            self._connected = False

    def is_connected(self):
        """检查是否已连接"""
        return self._connected

    # ==================== 数据采集相关方法 ====================

    def save_collection(self, collection_id: str, meta: dict):
        """
        保存采集元数据

        Args:
            collection_id: 采集ID
            meta: 元数据字典，包含name, duration等
        """
        if not self._connected:
            return False

        key = f"collection:{collection_id}:meta"
        meta['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._client.hset(key, mapping=meta)
        return True

    def get_collection_meta(self, collection_id: str) -> dict:
        """
        获取采集元数据

        Args:
            collection_id: 采集ID

        Returns:
            元数据字典
        """
        if not self._connected:
            return {}

        key = f"collection:{collection_id}:meta"
        return self._client.hgetall(key)

    def save_sample(self, collection_id: str, sample: dict):
        """
        保存单个样本数据

        Args:
            collection_id: 采集ID
            sample: 样本数据
        """
        if not self._connected:
            return False

        # 使用有序集合存储样本，以时间戳为分数
        key = f"collection:{collection_id}:samples"
        score = sample.get('timestamp', time.time())
        self._client.zadd(key, {json.dumps(sample): score})

        # 更新样本计数
        count_key = f"collection:{collection_id}:count"
        self._client.incr(count_key)

        return True

    def get_sample_count(self, collection_id: str) -> int:
        """
        获取采集的样本数量

        Args:
            collection_id: 采集ID

        Returns:
            样本数量
        """
        if not self._connected:
            return 0

        count_key = f"collection:{collection_id}:count"
        count = self._client.get(count_key)
        return int(count) if count else 0

    def get_collection_data(self, collection_id: str, start: int = 0, end: int = -1) -> List[dict]:
        """
        获取采集数据

        Args:
            collection_id: 采集ID
            start: 起始索引
            end: 结束索引，-1表示到最后

        Returns:
            样本数据列表
        """
        if not self._connected:
            return []

        key = f"collection:{collection_id}:samples"
        # zrange获取指定范围的元素
        if end == -1:
            data = self._client.zrange(key, start, -1)
        else:
            data = self._client.zrange(key, start, end)

        return [json.loads(item) for item in data]

    def get_collections_list(self) -> List[dict]:
        """
        获取所有采集列表

        Returns:
            采集信息列表，每个元素包含id, name, created_at, sample_count, status
        """
        if not self._connected:
            return []

        # 查找所有collection元数据key
        pattern = "collection:*:meta"
        keys = self._client.keys(pattern)

        collections = []
        for key in keys:
            # 提取collection_id
            collection_id = key.split(':')[1]
            meta = self._client.hgetall(key)
            count = self.get_sample_count(collection_id)

            collections.append({
                'id': collection_id,
                'name': meta.get('name', ''),
                'created_at': meta.get('created_at', ''),
                'sample_count': str(count),
                'status': meta.get('status', 'completed')
            })

        # 按创建时间排序
        collections.sort(key=lambda x: x['created_at'], reverse=True)
        return collections

    def delete_collection(self, collection_id: str) -> bool:
        """
        删除采集数据

        Args:
            collection_id: 采集ID

        Returns:
            是否删除成功
        """
        if not self._connected:
            return False

        # 删除元数据、样本和计数
        keys = [
            f"collection:{collection_id}:meta",
            f"collection:{collection_id}:samples",
            f"collection:{collection_id}:count"
        ]
        self._client.delete(*keys)
        return True

    # ==================== 通用数据操作方法 ====================

    def get_data(self, key: str) -> any:
        """
        获取数据

        Args:
            key: 键名

        Returns:
            数据值
        """
        if not self._connected:
            return None

        value = self._client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None

    def set_data(self, key: str, value: any):
        """
        设置数据

        Args:
            key: 键名
            value: 数据值
        """
        if not self._connected:
            return False

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        self._client.set(key, value)
        return True

    def delete_data(self, key: str) -> bool:
        """
        删除数据

        Args:
            key: 键名

        Returns:
            是否删除成功
        """
        if not self._connected:
            return False

        self._client.delete(key)
        return True

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名

        Returns:
            键是否存在
        """
        if not self._connected:
            return False

        return self._client.exists(key) > 0
