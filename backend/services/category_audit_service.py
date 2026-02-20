"""
Category-based bulk audit service for scraping and auditing multiple products.
Supports regulator-driven category audits across e-commerce platforms.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import Callable
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from backend.models import RiskLevel, URLAuditResult
from backend.services.url_audit_service import URLAuditService

logger = logging.getLogger(__name__)


class ProductCategory(str, Enum):
    """Predefined product categories for Legal Metrology compliance"""
    FOOD_OIL = "Food - Edible Oil"
    FOOD_PACKAGED = "Food - Packaged Items"
    ELECTRONICS = "Electronics"
    COSMETICS = "Cosmetics & Personal Care"
    IMPORTED_GOODS = "Imported Products"
    HOUSEHOLD = "Household Items"
    BEVERAGES = "Beverages"
    CUSTOM = "Custom Search"


# Category to search keywords mapping
CATEGORY_KEYWORDS = {
    ProductCategory.FOOD_OIL: ["sunflower oil", "cooking oil", "edible oil", "mustard oil", "groundnut oil"],
    ProductCategory.FOOD_PACKAGED: ["packaged food", "snacks", "biscuits", "noodles", "ready to eat"],
    ProductCategory.ELECTRONICS: ["mobile phone", "laptop", "headphones", "charger", "power bank"],
    ProductCategory.COSMETICS: ["face cream", "shampoo", "soap", "lotion", "skincare"],
    ProductCategory.IMPORTED_GOODS: ["imported", "foreign brand"],
    ProductCategory.HOUSEHOLD: ["detergent", "cleaning", "kitchen appliance"],
    ProductCategory.BEVERAGES: ["juice", "soft drink", "energy drink", "packaged water"],
}


@dataclass
class BulkAuditProgress:
    """Progress tracking for bulk audits"""
    total: int
    completed: int
    failed: int
    in_progress: bool
    results: list[URLAuditResult]
    errors: list[str]


class CategoryAuditService:
    """
    Service for category-based bulk product auditing.
    Enables regulators to audit multiple products from a category at once.
    """

    def __init__(self, max_workers: int = 5) -> None:
        self.url_audit_service = URLAuditService()
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def get_category_keywords(self, category: ProductCategory) -> list[str]:
        """Get search keywords for a category"""
        return CATEGORY_KEYWORDS.get(category, [])

    def search_product_urls(
        self,
        query: str,
        max_results: int = 10,
        marketplace: str = "amazon.in"
    ) -> list[str]:
        """
        Search for product URLs based on a query.
        Returns list of product page URLs to audit.
        """
        product_urls = []
        
        try:
            # Build search URL based on marketplace
            if "amazon" in marketplace.lower():
                search_url = f"https://www.amazon.in/s?k={quote_plus(query)}"
            elif "flipkart" in marketplace.lower():
                search_url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
            else:
                # Generic search
                search_url = f"https://www.google.com/search?q={quote_plus(query)}+buy+online"
            
            response = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract product URLs based on marketplace
            if "amazon" in marketplace.lower():
                # Amazon product links
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/dp/" in href or "/gp/product/" in href:
                        full_url = urljoin("https://www.amazon.in", href.split("?")[0])
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            if len(product_urls) >= max_results:
                                break
            
            elif "flipkart" in marketplace.lower():
                # Flipkart product links
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/p/" in href:
                        full_url = urljoin("https://www.flipkart.com", href)
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                            if len(product_urls) >= max_results:
                                break
            
            logger.info(f"Found {len(product_urls)} product URLs for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching for products: {e}")
        
        return product_urls[:max_results]

    def audit_single_url(self, url: str, seller_id: str) -> tuple[URLAuditResult | None, str | None]:
        """
        Audit a single URL. Returns (result, error).
        """
        try:
            result = self.url_audit_service.audit(url=url, seller_id=seller_id)
            return result, None
        except Exception as e:
            logger.error(f"Failed to audit {url}: {e}")
            return None, f"Failed to audit {url}: {str(e)}"

    def bulk_audit_urls(
        self,
        urls: list[str],
        seller_id: str = "regulator-audit",
        progress_callback: Callable[[BulkAuditProgress], None] | None = None
    ) -> BulkAuditProgress:
        """
        Audit multiple URLs in parallel using ThreadPoolExecutor.
        """
        progress = BulkAuditProgress(
            total=len(urls),
            completed=0,
            failed=0,
            in_progress=True,
            results=[],
            errors=[]
        )
        
        if not urls:
            progress.in_progress = False
            return progress
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.audit_single_url, url, seller_id): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result, error = future.result()
                    if result:
                        progress.results.append(result)
                        progress.completed += 1
                    else:
                        progress.failed += 1
                        if error:
                            progress.errors.append(error)
                except Exception as e:
                    progress.failed += 1
                    progress.errors.append(f"Unexpected error for {url}: {str(e)}")
                
                # Callback for progress updates
                if progress_callback:
                    progress_callback(progress)
        
        progress.in_progress = False
        return progress

    def audit_by_category(
        self,
        category: ProductCategory,
        max_products: int = 20,
        seller_id: str = "regulator-audit",
        custom_keyword: str | None = None,
        marketplace: str = "amazon.in"
    ) -> BulkAuditProgress:
        """
        Audit products by category.
        Searches for products in the category and audits them in parallel.
        """
        # Get search keywords
        if category == ProductCategory.CUSTOM and custom_keyword:
            keywords = [custom_keyword]
        else:
            keywords = self.get_category_keywords(category)
        
        if not keywords:
            return BulkAuditProgress(
                total=0,
                completed=0,
                failed=0,
                in_progress=False,
                results=[],
                errors=["No keywords found for category"]
            )
        
        # Collect product URLs from all keywords
        all_urls: list[str] = []
        products_per_keyword = max(2, max_products // len(keywords))
        
        for keyword in keywords:
            urls = self.search_product_urls(
                query=keyword,
                max_results=products_per_keyword,
                marketplace=marketplace
            )
            for url in urls:
                if url not in all_urls:
                    all_urls.append(url)
                    if len(all_urls) >= max_products:
                        break
            if len(all_urls) >= max_products:
                break
        
        logger.info(f"Starting bulk audit for category {category.value} with {len(all_urls)} products")
        
        # Audit all collected URLs
        return self.bulk_audit_urls(urls=all_urls, seller_id=seller_id)


class CategoryAnalyticsService:
    """
    Service for generating category-wise compliance analytics.
    """

    def __init__(self, db_client) -> None:
        self.db = db_client

    async def get_category_stats(self) -> dict:
        """Get compliance statistics grouped by category"""
        reports = await self.db.get_reports()
        
        category_stats: dict[str, dict] = {}
        
        for report in reports:
            # Try to infer category from product title/description
            category = self._infer_category(report)
            
            if category not in category_stats:
                category_stats[category] = {
                    "total": 0,
                    "compliant": 0,
                    "moderate_risk": 0,
                    "high_risk": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            stats = category_stats[category]
            stats["total"] += 1
            stats["scores"].append(report.get("compliance_score", report.get("score", 0)))
            
            risk_level = report.get("risk_level", "")
            if risk_level == "Compliant":
                stats["compliant"] += 1
            elif risk_level == "Moderate Risk":
                stats["moderate_risk"] += 1
            else:
                stats["high_risk"] += 1
        
        # Calculate averages
        for category, stats in category_stats.items():
            if stats["scores"]:
                stats["avg_score"] = round(sum(stats["scores"]) / len(stats["scores"]), 1)
            del stats["scores"]  # Remove raw scores from output
            
            # Calculate compliance rate
            stats["compliance_rate"] = round(
                (stats["compliant"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1
            )
        
        return category_stats

    def _infer_category(self, report: dict) -> str:
        """Infer product category from report data"""
        title = (report.get("scraped_data", {}).get("title") or 
                 report.get("product_name") or "").lower()
        description = (report.get("scraped_data", {}).get("description") or "").lower()
        
        combined = f"{title} {description}"
        
        # Category inference rules
        if any(word in combined for word in ["oil", "ghee", "cooking"]):
            return "Food - Edible Oil"
        elif any(word in combined for word in ["mobile", "phone", "laptop", "charger", "electronic"]):
            return "Electronics"
        elif any(word in combined for word in ["cream", "lotion", "shampoo", "soap", "cosmetic"]):
            return "Cosmetics"
        elif any(word in combined for word in ["juice", "drink", "water", "beverage"]):
            return "Beverages"
        elif any(word in combined for word in ["imported", "foreign"]):
            return "Imported Goods"
        elif any(word in combined for word in ["food", "snack", "biscuit", "noodle"]):
            return "Food - Packaged"
        else:
            return "Other"

    async def get_risk_distribution(self) -> dict:
        """Get risk level distribution for charts"""
        reports = await self.db.get_reports()
        
        distribution = {
            "Compliant": 0,
            "Moderate Risk": 0,
            "High Risk": 0
        }
        
        for report in reports:
            risk_level = report.get("risk_level", "High Risk")
            if risk_level in distribution:
                distribution[risk_level] += 1
        
        return distribution

    async def get_violation_trends(self) -> list[dict]:
        """Get most common violations with counts"""
        reports = await self.db.get_reports()
        
        violation_counter: dict[str, int] = {}
        
        for report in reports:
            for violation in report.get("violations", []):
                field = violation.get("field", "unknown")
                message = violation.get("message", violation.get("code", "Unknown"))
                key = f"{field}: {message}"
                violation_counter[key] = violation_counter.get(key, 0) + 1
        
        # Sort by count and return top 10
        sorted_violations = sorted(
            violation_counter.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return [
            {"violation": key, "count": count}
            for key, count in sorted_violations
        ]

    async def get_compliance_timeline(self, days: int = 30) -> list[dict]:
        """Get compliance scores over time for trend charts"""
        from datetime import datetime, timedelta
        
        reports = await self.db.get_reports()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Group by date
        daily_stats: dict[str, dict] = {}
        
        for report in reports:
            created_at = report.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    continue
            
            if created_at and created_at >= cutoff_date:
                date_key = created_at.strftime("%Y-%m-%d")
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "date": date_key,
                        "total": 0,
                        "compliant": 0,
                        "scores": []
                    }
                
                daily_stats[date_key]["total"] += 1
                daily_stats[date_key]["scores"].append(
                    report.get("compliance_score", report.get("score", 0))
                )
                if report.get("risk_level") == "Compliant":
                    daily_stats[date_key]["compliant"] += 1
        
        # Calculate averages and format output
        result = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            result.append({
                "date": date_key,
                "total_audited": stats["total"],
                "compliant_count": stats["compliant"],
                "avg_compliance_score": round(avg_score, 1)
            })
        
        return result
