import time
import json
import logging
from typing import Optional, Any
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._in_memory_store: dict = {}
        self._in_memory_expiry: dict = {}
        self._in_memory_hits: int = 0
        self._in_memory_misses: int = 0
        self._connected: bool = False
        self._connect()

    def _connect(self):
        try:
            r = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5
            )
            r.ping()
            self.redis_client = r
            self._connected = True
            logger.info("Successfully connected to Redis at %s", settings.REDIS_URL)
        except Exception as e:
            self.redis_client = None
            self._connected = False
            logger.warning("Redis connection failed (%s). Falling back to in-memory cache.", str(e))

    def is_connected(self) -> bool:
        if self.redis_client:
            try:
                self.redis_client.ping()
                self._connected = True
                return True
            except Exception:
                self._connected = False
                return False
        return False

    def get(self, key: str) -> Optional[str]:
        if self.is_connected() and self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val is not None:
                    self.redis_client.incr("stats:cache_hits")
                    return val
                else:
                    self.redis_client.incr("stats:cache_misses")
                    return None
            except Exception:
                pass

        # In-memory fallback
        now = time.time()
        if key in self._in_memory_store:
            exp = self._in_memory_expiry.get(key)
            if exp is None or exp > now:
                self._in_memory_hits += 1
                return self._in_memory_store[key]
            else:
                del self._in_memory_store[key]
                if key in self._in_memory_expiry:
                    del self._in_memory_expiry[key]
        self._in_memory_misses += 1
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        ttl = ex if ex is not None else settings.CACHE_DEFAULT_TTL_SECONDS
        if self.is_connected() and self.redis_client:
            try:
                self.redis_client.set(key, value, ex=ttl)
                return True
            except Exception:
                pass

        # In-memory fallback
        self._in_memory_store[key] = value
        self._in_memory_expiry[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        if self.is_connected() and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        self._in_memory_store.pop(key, None)
        self._in_memory_expiry.pop(key, None)
        return True

    def delete_pattern(self, pattern: str) -> int:
        count = 0
        if self.is_connected() and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count += self.redis_client.delete(*keys)
            except Exception:
                pass

        # Match and clear from in-memory store
        prefix = pattern.rstrip("*")
        to_del = [k for k in self._in_memory_store if k.startswith(prefix)]
        for k in to_del:
            self._in_memory_store.pop(k, None)
            self._in_memory_expiry.pop(k, None)
            count += 1
        return count

    def get_stats(self) -> dict:
        hits = 0
        misses = 0
        keys_count = 0
        status = "fallback_in_memory"

        if self.is_connected() and self.redis_client:
            try:
                h = self.redis_client.get("stats:cache_hits")
                m = self.redis_client.get("stats:cache_misses")
                hits = int(h) if h else 0
                misses = int(m) if m else 0
                keys_count = len(self.redis_client.keys("availability:*")) + len(self.redis_client.keys("nearest:*"))
                status = "connected"
            except Exception:
                status = "degraded"

        if status != "connected":
            hits = self._in_memory_hits
            misses = self._in_memory_misses
            keys_count = len(self._in_memory_store)

        total = hits + misses
        hit_ratio = round((hits / total) if total > 0 else 0.0, 3)
        return {
            "hits": hits,
            "misses": misses,
            "keys_count": keys_count,
            "hit_ratio": hit_ratio,
            "status": status
        }

    def check_rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """
        Fixed window rate limiter.
        Returns True if allowed, False if exceeded.
        """
        key = f"ratelimit:{identifier}:{int(time.time() // window)}"
        if self.is_connected() and self.redis_client:
            try:
                current = self.redis_client.incr(key)
                if current == 1:
                    self.redis_client.expire(key, window + 1)
                return current <= limit
            except Exception:
                pass

        # In-memory fallback
        now = time.time()
        bucket = int(now // window)
        mem_key = f"rl:{identifier}:{bucket}"
        val = self._in_memory_store.get(mem_key, 0)
        if isinstance(val, int):
            val += 1
        else:
            val = 1
        self._in_memory_store[mem_key] = val
        self._in_memory_expiry[mem_key] = (bucket + 1) * window
        return val <= limit


cache_client = CacheClient()
