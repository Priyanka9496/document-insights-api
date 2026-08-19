import redis.asyncio as redis


def create_redis_client(redis_url):
    return redis.from_url(
        redis_url,
        decode_responses=True
    )