"""
Crawler Service - Scalable Web Crawling Microservice

This service handles web crawling using both Scrapy and async requests.
Supports bulk URL ingestion, pagination, and multiple product categories.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, str(__file__).replace("services/crawler-service/app/main.py", ""))

from shared.utils.logger import setup_logging, get_logger
from shared.database.mongodb import mongodb_client
from shared.database.redis_client import redis_client, Queues

# Setup logging
setup_logging("crawler-service", level="INFO")
logger = get_logger(__name__)


# Request/Response Models
class CrawlRequest(BaseModel):
    url: str
    seller_id: str = "default"
    category: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)


class BulkCrawlRequest(BaseModel):
    urls: list[str]
    seller_id: str = "default"
    category: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)


class CrawlJobResponse(BaseModel):
    job_id: str
    status: str
    url: str
    message: str


class BulkCrawlResponse(BaseModel):
    task_id: str
    status: str
    total_urls: int
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Crawler Service...")
    try:
        await mongodb_client.connect()
        await redis_client.connect()
        logger.info("Crawler Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Crawler Service...")
    await mongodb_client.disconnect()
    await redis_client.disconnect()


app = FastAPI(
    title="Crawler Service",
    description="Scalable web crawling microservice for product data extraction",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "crawler-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/crawl", response_model=CrawlJobResponse)
async def crawl_url(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Submit a single URL for crawling.
    
    The URL is added to the crawl queue and processed asynchronously.
    """
    job_id = str(uuid.uuid4())
    
    # Create crawl job
    crawl_job = {
        "job_id": job_id,
        "url": request.url,
        "seller_id": request.seller_id,
        "category": request.category,
        "priority": request.priority,
        "status": "pending",
        "retry_count": 0,
        "max_retries": 3,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Save to MongoDB
    await mongodb_client.update_one(
        "crawl_queue",
        {"url": request.url},
        crawl_job,
        upsert=True,
    )
    
    # Push to Redis queue
    await redis_client.queue_push(Queues.CRAWL, crawl_job)
    
    logger.info(f"Crawl job created: {job_id} for URL: {request.url}")
    
    return CrawlJobResponse(
        job_id=job_id,
        status="queued",
        url=request.url,
        message="URL added to crawl queue",
    )


@app.post("/crawl/bulk", response_model=BulkCrawlResponse)
async def bulk_crawl(request: BulkCrawlRequest, background_tasks: BackgroundTasks):
    """
    Submit multiple URLs for crawling.
    
    All URLs are added to the crawl queue and processed in parallel.
    """
    if len(request.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs per request")
    
    task_id = str(uuid.uuid4())
    
    # Create bulk task record
    bulk_task = {
        "task_id": task_id,
        "total_urls": len(request.urls),
        "completed": 0,
        "failed": 0,
        "status": "processing",
        "seller_id": request.seller_id,
        "category": request.category,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    await mongodb_client.insert_one("bulk_tasks", bulk_task)
    
    # Queue all URLs
    for url in request.urls:
        job_id = str(uuid.uuid4())
        crawl_job = {
            "job_id": job_id,
            "task_id": task_id,
            "url": url,
            "seller_id": request.seller_id,
            "category": request.category,
            "priority": request.priority,
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await mongodb_client.update_one(
            "crawl_queue",
            {"url": url},
            crawl_job,
            upsert=True,
        )
        
        await redis_client.queue_push(Queues.CRAWL, crawl_job)
    
    logger.info(f"Bulk crawl task created: {task_id} with {len(request.urls)} URLs")
    
    return BulkCrawlResponse(
        task_id=task_id,
        status="processing",
        total_urls=len(request.urls),
        message=f"Added {len(request.urls)} URLs to crawl queue",
    )


@app.get("/crawl/status/{job_id}")
async def get_crawl_status(job_id: str):
    """Get status of a crawl job."""
    job = await mongodb_client.find_one("crawl_queue", {"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@app.get("/crawl/bulk/status/{task_id}")
async def get_bulk_status(task_id: str):
    """Get status of a bulk crawl task."""
    task = await mongodb_client.find_one("bulk_tasks", {"task_id": task_id})
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.get("/queue/stats")
async def get_queue_stats():
    """Get crawl queue statistics."""
    pending = await mongodb_client.count("crawl_queue", {"status": "pending"})
    processing = await mongodb_client.count("crawl_queue", {"status": "processing"})
    completed = await mongodb_client.count("crawl_queue", {"status": "completed"})
    failed = await mongodb_client.count("crawl_queue", {"status": "failed"})
    
    queue_length = await redis_client.queue_length(Queues.CRAWL)
    
    return {
        "queue_length": queue_length,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total": pending + processing + completed + failed,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
