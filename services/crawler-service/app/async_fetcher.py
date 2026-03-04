"""
Async URL Fetcher for high-performance crawling.

Uses aiohttp for concurrent requests with rate limiting and retry support.
"""
import asyncio
import random
from typing import Any, Optional
from dataclasses import dataclass
import logging

import aiohttp
from aiohttp import ClientTimeout, ClientError

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of a URL fetch operation."""
    url: str
    status_code: int
    content: str
    headers: dict[str, str]
    success: bool
    error: Optional[str] = None
    retry_count: int = 0


class AsyncFetcher:
    """High-performance async URL fetcher with rate limiting."""
    
    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]
    
    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
    ):
        self.max_concurrent = max_concurrent
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers with random user agent."""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Google Chrome";v="121", "Chromium";v="121", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.google.com/",
        }
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session."""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            enable_cleanup_closed=True,
        )
        return aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
        )
    
    async def __aenter__(self):
        self._session = await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def fetch_one(
        self,
        url: str,
        retry_count: int = 0,
    ) -> FetchResult:
        """
        Fetch a single URL with retry support.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
        
        Returns:
            FetchResult with content or error
        """
        async with self._semaphore:
            try:
                # Add delay for rate limiting
                if retry_count > 0:
                    delay = random.uniform(2, 5) * retry_count
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(self.rate_limit_delay * random.uniform(0.5, 1.5))
                
                headers = self._get_headers()
                
                async with self._session.get(url, headers=headers, ssl=False) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        if retry_count < self.max_retries:
                            logger.warning(f"Rate limited for {url}, retrying...")
                            return await self.fetch_one(url, retry_count + 1)
                    
                    # Handle bot detection
                    if response.status in [503, 529]:
                        if retry_count < self.max_retries:
                            logger.warning(f"Bot detection for {url}, retrying...")
                            return await self.fetch_one(url, retry_count + 1)
                    
                    content = await response.text()
                    
                    return FetchResult(
                        url=url,
                        status_code=response.status,
                        content=content,
                        headers=dict(response.headers),
                        success=response.status == 200,
                        retry_count=retry_count,
                    )
            
            except asyncio.TimeoutError:
                if retry_count < self.max_retries:
                    logger.warning(f"Timeout for {url}, retrying...")
                    return await self.fetch_one(url, retry_count + 1)
                return FetchResult(
                    url=url,
                    status_code=0,
                    content="",
                    headers={},
                    success=False,
                    error="Timeout",
                    retry_count=retry_count,
                )
            
            except ClientError as e:
                if retry_count < self.max_retries:
                    logger.warning(f"Client error for {url}: {e}, retrying...")
                    return await self.fetch_one(url, retry_count + 1)
                return FetchResult(
                    url=url,
                    status_code=0,
                    content="",
                    headers={},
                    success=False,
                    error=str(e),
                    retry_count=retry_count,
                )
            
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return FetchResult(
                    url=url,
                    status_code=0,
                    content="",
                    headers={},
                    success=False,
                    error=str(e),
                    retry_count=retry_count,
                )
    
    async def fetch_many(
        self,
        urls: list[str],
        callback: Optional[callable] = None,
    ) -> list[FetchResult]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            callback: Optional callback for each completed fetch
        
        Returns:
            List of FetchResults
        """
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.fetch_one(url))
            tasks.append(task)
        
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            
            if callback:
                await callback(result)
            
            logger.info(f"Fetched: {result.url} - Status: {result.status_code}")
        
        return results


class URLQueue:
    """Priority queue for URL crawling."""
    
    def __init__(self, max_size: int = 10000):
        self._queue: list[tuple[int, str, dict]] = []  # (priority, url, metadata)
        self._seen: set[str] = set()
        self.max_size = max_size
    
    def add(
        self,
        url: str,
        priority: int = 1,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Add URL to queue if not seen before."""
        # Normalize URL
        url = url.rstrip("/")
        
        if url in self._seen:
            return False
        
        if len(self._queue) >= self.max_size:
            logger.warning("Queue full, dropping lowest priority item")
            self._queue.sort(key=lambda x: x[0], reverse=True)
            self._queue.pop()
        
        self._seen.add(url)
        self._queue.append((-priority, url, metadata or {}))  # Negative for max-heap behavior
        self._queue.sort(key=lambda x: x[0])
        
        return True
    
    def pop(self) -> Optional[tuple[str, dict]]:
        """Get highest priority URL."""
        if not self._queue:
            return None
        
        _, url, metadata = self._queue.pop(0)
        return url, metadata
    
    def peek(self, n: int = 10) -> list[tuple[str, dict]]:
        """Peek at top n URLs."""
        return [(url, meta) for _, url, meta in self._queue[:n]]
    
    def __len__(self) -> int:
        return len(self._queue)
    
    def __contains__(self, url: str) -> bool:
        return url.rstrip("/") in self._seen
