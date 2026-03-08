import time
from collections import OrderedDict
from dataclasses import dataclass
import os
import redis.asyncio as redis
from .config import Settings

@dataclass
class _CacheEntry:
    value: str
    expires_at: float
'''
class TTLAltCache:
    def __init__(self, ttl_sec: int, max_entries: int):
        self.ttl_sec = ttl_sec
        self.max_entries = max_entries
        self._store = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > self.ttl_sec:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: str):
        if len(self._store) >= self.max_entries:
            first_key = next(iter(self._store))
            del self._store[first_key]
        self._store[key] = {
            "value": value,
            "timestamp": time.time()
        }
'''

class RedisCacheManager:
    def __init__(self, settings: Settings):
        self._redis = redis.Redis(
            host = settings.redis_host,
            port = settings.redis_port,
            decode_responses = True
        )
        self.ttl = settings.cache_ttl_sec
    
    async def get(self, key: str) -> str | None:
        try:
            return await self._redis.get(key)
        except Exception as e:
            print(f"Redis 조회 에러: {e}")
            return None
    
    async def set(self, key: str, value: str):
        try:
            await self._redis.setex(key, self.ttl, value)
        except Exception as e:
            print(f"Redis 저장 에러: {e}")
    
    async def close(self):
        await self._redis.aclose()