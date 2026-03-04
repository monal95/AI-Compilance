"""MongoDB database client with connection pooling and async support."""
import logging
from typing import Any, Optional
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Async MongoDB client with connection pooling."""
    
    _instance: Optional["MongoDBClient"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(
        self,
        url: str = "mongodb://localhost:27017",
        database: str = "legal_metrology",
        max_pool_size: int = 100,
        min_pool_size: int = 10,
        timeout_ms: int = 5000,
    ) -> None:
        """Connect to MongoDB with connection pooling."""
        try:
            self._client = AsyncIOMotorClient(
                url,
                maxPoolSize=max_pool_size,
                minPoolSize=min_pool_size,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
            )
            # Verify connection
            await self._client.admin.command("ping")
            self._db = self._client[database]
            logger.info(f"Connected to MongoDB: {database}")
            
            # Create indexes
            await self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _create_indexes(self) -> None:
        """Create database indexes for better query performance."""
        try:
            # Products collection
            await self._db.products.create_index("product_id", unique=True)
            await self._db.products.create_index("url")
            await self._db.products.create_index("category")
            await self._db.products.create_index("marketplace")
            await self._db.products.create_index("crawl_status")
            await self._db.products.create_index("created_at")
            
            # Audits collection
            await self._db.audits.create_index("audit_id", unique=True)
            await self._db.audits.create_index("product_id")
            await self._db.audits.create_index("seller_id")
            await self._db.audits.create_index("risk_level")
            await self._db.audits.create_index("created_at")
            await self._db.audits.create_index([("seller_id", 1), ("created_at", -1)])
            
            # Rules collection
            await self._db.rules.create_index("rule_id", unique=True)
            await self._db.rules.create_index("category")
            await self._db.rules.create_index("field")
            await self._db.rules.create_index("active")
            
            # Crawl queue collection
            await self._db.crawl_queue.create_index("url")
            await self._db.crawl_queue.create_index("status")
            await self._db.crawl_queue.create_index("priority")
            await self._db.crawl_queue.create_index([("status", 1), ("priority", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("Disconnected from MongoDB")
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
    
    # Collection shortcuts
    @property
    def products(self):
        return self.db.products
    
    @property
    def audits(self):
        return self.db.audits
    
    @property
    def rules(self):
        return self.db.rules
    
    @property
    def crawl_queue(self):
        return self.db.crawl_queue
    
    # Generic CRUD operations
    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        """Insert a single document."""
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection: str, documents: list[dict[str, Any]]) -> list[str]:
        """Insert multiple documents."""
        result = await self.db[collection].insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(
        self,
        collection: str,
        query: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Find a single document."""
        projection = projection or {"_id": 0}
        return await self.db[collection].find_one(query, projection)
    
    async def find_many(
        self,
        collection: str,
        query: dict[str, Any],
        projection: Optional[dict[str, Any]] = None,
        sort: Optional[list[tuple]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Find multiple documents with pagination."""
        projection = projection or {"_id": 0}
        cursor = self.db[collection].find(query, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        
        cursor = cursor.skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def update_one(
        self,
        collection: str,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> bool:
        """Update a single document."""
        result = await self.db[collection].update_one(
            query,
            {"$set": update},
            upsert=upsert,
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def delete_one(self, collection: str, query: dict[str, Any]) -> bool:
        """Delete a single document."""
        result = await self.db[collection].delete_one(query)
        return result.deleted_count > 0
    
    async def count(self, collection: str, query: dict[str, Any]) -> int:
        """Count documents matching query."""
        return await self.db[collection].count_documents(query)
    
    async def aggregate(
        self,
        collection: str,
        pipeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Run aggregation pipeline."""
        cursor = self.db[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)


# Singleton instance
mongodb_client = MongoDBClient()


@asynccontextmanager
async def get_database():
    """Context manager for database operations."""
    yield mongodb_client
