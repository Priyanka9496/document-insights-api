import json
import logging
from redis.exceptions import RedisError
from app.schemas.document import Summary

logger = logging.getLogger(__name__)


class SummaryCache:

    def __init__(self, redis_client, ttl):
        self.redis_client = redis_client
        self.ttl = ttl

    def _get_key(self, user_id, content_hash):
        return f"summary:{user_id}:{content_hash}"

    async def get(self, user_id, content_hash):
        key = self._get_key(user_id, content_hash)

        try:
            cached_value = await self.redis_client.get(key)
        except RedisError:
            logger.warning(
                "Failed to read summary from Redis cache",
                exc_info=True
            )
            return None

        if cached_value is None:
            return None

        try:
            return Summary.model_validate(
                json.loads(cached_value)
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "Invalid summary found in Redis cache",
                exc_info=True
            )
            return None

    async def set(self, user_id, content_hash, summary):
        key = self._get_key(user_id, content_hash)

        try:
            await self.redis_client.set(
                key,
                json.dumps(summary),
                ex=self.ttl
            )
        except RedisError:
            logger.warning(
                "Failed to write summary to Redis cache",
                exc_info=True
            )