"""Redis client for caching and message queuing."""
import json
import logging
from typing import Any, Optional
from datetime import timedelta

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for caching and queuing."""
    
    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 100,
    ) -> None:
        """Connect to Redis server."""
        try:
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                max_connections=max_connections,
                decode_responses=True,
            )
            # Verify connection
            await self._client.ping()
            logger.info(f"Connected to Redis: {host}:{port}")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Redis")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client
    
    # Caching operations
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set cached value with optional TTL (seconds)."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if ttl:
                return await self.client.setex(key, ttl, value)
            return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def cache_delete(self, key: str) -> bool:
        """Delete cached value."""
        return await self.client.delete(key) > 0
    
    async def cache_exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0
    
    async def cache_invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = await self.client.keys(pattern)
        if keys:
            return await self.client.delete(*keys)
        return 0
    
    # Queue operations
    async def queue_push(self, queue_name: str, item: dict[str, Any]) -> int:
        """Push item to queue (right side)."""
        return await self.client.rpush(queue_name, json.dumps(item))
    
    async def queue_push_priority(self, queue_name: str, item: dict[str, Any]) -> int:
        """Push item to front of queue (left side) for priority."""
        return await self.client.lpush(queue_name, json.dumps(item))
    
    async def queue_pop(self, queue_name: str, timeout: int = 0) -> Optional[dict[str, Any]]:
        """Pop item from queue (blocking with timeout)."""
        result = await self.client.blpop(queue_name, timeout=timeout)
        if result:
            _, value = result
            return json.loads(value)
        return None
    
    async def queue_length(self, queue_name: str) -> int:
        """Get queue length."""
        return await self.client.llen(queue_name)
    
    async def queue_peek(self, queue_name: str, count: int = 10) -> list[dict[str, Any]]:
        """Peek at queue items without removing."""
        items = await self.client.lrange(queue_name, 0, count - 1)
        return [json.loads(item) for item in items]
    
    # Rate limiting
    async def rate_limit_check(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.
        Returns (is_allowed, remaining_requests).
        """
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window_seconds)
        
        remaining = max(0, limit - current)
        return current <= limit, remaining
    
    # Pub/Sub operations
    async def publish(self, channel: str, message: dict[str, Any]) -> int:
        """Publish message to channel."""
        return await self.client.publish(channel, json.dumps(message))
    
    def subscribe(self, *channels: str):
        """Subscribe to channels (returns pubsub object)."""
        pubsub = self.client.pubsub()
        return pubsub
    
    # Distributed locks
    async def acquire_lock(
        self,
        lock_name: str,
        timeout: int = 30,
    ) -> bool:
        """Acquire distributed lock."""
        return await self.client.set(
            f"lock:{lock_name}",
            "1",
            nx=True,
            ex=timeout,
        )
    
    async def release_lock(self, lock_name: str) -> bool:
        """Release distributed lock."""
        return await self.client.delete(f"lock:{lock_name}") > 0


# Singleton instance
redis_client = RedisClient()


# Queue names
class Queues:
    CRAWL = "queue:crawl"
    OCR = "queue:ocr"
    NLP = "queue:nlp"
    COMPLIANCE = "queue:compliance"
    REPORT = "queue:report"


# Cache key prefixes
class CacheKeys:
    PRODUCT = "cache:product:"
    AUDIT = "cache:audit:"
    RULES = "cache:rules:"
    ANALYTICS = "cache:analytics:"
    OCR_RESULT = "cache:ocr:"
