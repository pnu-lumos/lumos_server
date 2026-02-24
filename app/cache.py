import time
from collections import OrderedDict
from dataclasses import dataclass
import os
from .config import Settings

@dataclass
class _CacheEntry:
    value: str
    expires_at: float

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
class CacheManager:
    def __init__(self):
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 0000))
        self._redis = redis.Redis(host = host, port = port, decode_responses = True)
    
    async def get(self, key: str):
        return await self._redis.get(key)
    
    async def set(self, key: str, value: str, expire: int = 86400):
        await self._redis.set(key, value, ex = expire)
        '''
