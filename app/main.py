from fastapi import FastAPI
from app.config import get_settings
from app.database import create_mongo_client, create_indexes
from contextlib import asynccontextmanager
from app.routers.documents import router as documents_router
from app.routers.users import router as users_router
from app.redis_client import create_redis_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client = create_mongo_client(settings.mongodb_url)
    redis_client = create_redis_client(settings.redis_url)

    database = mongo_client[settings.mongodb_database]

    await redis_client.ping()
    await database.command("ping")
    await create_indexes(database)

    app.state.redis = redis_client
    app.state.mongo_client = mongo_client
    app.state.database = database

    yield

    await mongo_client.close()
    await redis_client.aclose()
    await mongo_client.close()

app = FastAPI(
    title="Document Insights API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(documents_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "message": "Document Insights API is running",
        "environment": settings.app_env
    }
