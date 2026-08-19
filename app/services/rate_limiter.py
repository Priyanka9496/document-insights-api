ACQUIRE_SCRIPT = """
local current = tonumber(redis.call("GET", KEYS[1]) or "0")
local limit = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

if current >= limit then
    return 0
end

redis.call("INCR", KEYS[1])
redis.call("EXPIRE", KEYS[1], ttl)

return 1
"""

RELEASE_SCRIPT = """
local current = tonumber(redis.call("GET", KEYS[1]) or "0")

if current <= 1 then
    redis.call("DEL", KEYS[1])
    return 0
end

return redis.call("DECR", KEYS[1])
"""


class ActiveJobLimiter:

    def __init__(self, redis_client, limit, ttl):
        self.redis_client = redis_client
        self.limit = limit
        self.ttl = ttl

    async def acquire(self, user_id):
        key = f"active_jobs:{user_id}"

        result = await self.redis_client.eval(
            ACQUIRE_SCRIPT,
            1,
            key,
            self.limit,
            self.ttl
        )

        return result == 1

    async def release(self, user_id):
        key = f"active_jobs:{user_id}"

        await self.redis_client.eval(
            RELEASE_SCRIPT,
            1,
            key
        )