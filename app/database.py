from pymongo import AsyncMongoClient
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient


def create_mongo_client(mongodb_url: str):
    return AsyncMongoClient(mongodb_url, tz_aware=True)


async def create_indexes(database):
    collection = database["documents"]

    await collection.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )

    await collection.create_index(
        [
            ("user_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ]
    )

    await collection.create_index(
        [("status", ASCENDING), ("created_at", ASCENDING)]
    )

    await collection.create_index(
        [
            ("user_id", ASCENDING),
            ("content_hash", ASCENDING),
            ("status", ASCENDING)
        ]
    )