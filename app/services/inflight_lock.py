import logging
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class InFlightLockUnavailable(Exception):
    pass


class InFlightDocumentLock:

    def __init__(self, redis_client, ttl):
        self.redis_client = redis_client
        self.ttl = ttl

    def _get_key(self, content_hash):
        return f"processing:{content_hash}"

    async def acquire(self, content_hash):
        key = self._get_key(content_hash)

        try:
            result = await self.redis_client.set(
                key,
                "1",
                nx=True,
                ex=self.ttl
            )
        except RedisError as error:
            raise InFlightLockUnavailable() from error

        return bool(result)

    async def release(self, content_hash):
        key = self._get_key(content_hash)

        try:
            await self.redis_client.delete(key)
        except RedisError:
            logger.warning(
                "Failed to release in-flight document lock",
                exc_info=True
            )