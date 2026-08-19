from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError


router = APIRouter(
    tags=["health"]
)


@router.get("/health")
async def health_check(request: Request):
    mongo_healthy = False
    redis_healthy = False

    try:
        await request.app.state.database.command("ping")
        mongo_healthy = True
    except Exception:
        mongo_healthy = False

    try:
        await request.app.state.redis.ping()
        redis_healthy = True
    except RedisError:
        redis_healthy = False

    healthy = mongo_healthy and redis_healthy

    response = {
        "status": "healthy" if healthy else "unhealthy",
        "mongodb": "healthy" if mongo_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy"
    }

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=response
    )