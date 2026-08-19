from fastapi import FastAPI
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Document Insights API",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Document Insights API is running",
        "environment": settings.app_env
    }
