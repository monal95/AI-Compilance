from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "legal_metrology"


settings = Settings()


class InMemoryCollection:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    async def insert_one(self, item: dict[str, Any]) -> None:
        self._items.append(item)

    async def find_all(self) -> list[dict[str, Any]]:
        return self._items

    async def find_one(self, product_id: str) -> dict[str, Any] | None:
        for item in self._items:
            if item.get("product_id") == product_id:
                return item
        return None


class DatabaseClient:
    def __init__(self) -> None:
        self._fallback = InMemoryCollection()
        self._collection = None

    async def connect(self) -> None:
        try:
            client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1500)
            await client.server_info()
            db = client[settings.mongodb_db]
            self._collection = db["compliance_reports"]
        except Exception:
            self._collection = None

    async def save_report(self, payload: dict[str, Any]) -> None:
        if self._collection is not None:
            await self._collection.insert_one(payload)
            return
        await self._fallback.insert_one(payload)

    async def get_reports(self) -> list[dict[str, Any]]:
        if self._collection is not None:
            cursor = self._collection.find({}, {"_id": 0})
            return await cursor.to_list(length=1000)
        return await self._fallback.find_all()

    async def get_product(self, product_id: str) -> dict[str, Any] | None:
        if self._collection is not None:
            return await self._collection.find_one({"product_id": product_id}, {"_id": 0})
        return await self._fallback.find_one(product_id)


db_client = DatabaseClient()
