from urllib.parse import urljoin
import re
import logging

import requests
from bs4 import BeautifulSoup
from requests import exceptions as request_exceptions

from backend.models import ScrapedProductData

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _first_non_empty(self, values: list[str | None]) -> str:
        for item in values:
            if item and item.strip():
                return item.strip()
        return ""

    def _is_amazon_url(self, url: str) -> bool:
        return "amazon.in" in url or "amazon.com" in url

    def _is_flipkart_url(self, url: str) -> bool:
        return "flipkart.com" in url

    def _extract_amazon_data(self, soup: BeautifulSoup, url: str) -> ScrapedProductData:
        """Extract product data from Amazon product pages with specialized selectors."""
        
        # Extract title - Amazon specific selectors
        title = self._first_non_empty([
            soup.find("span", {"id": "productTitle"}).get_text(strip=True) if soup.find("span", {"id": "productTitle"}) else None,
            soup.find("h1", {"id": "title"}).get_text(strip=True) if soup.find("h1", {"id": "title"}) else None,
            soup.find("meta", property="og:title").get("content") if soup.find("meta", property="og:title") else None,
        ])
        logger.info(f"Amazon title extracted: {title[:100] if title else 'None'}...")

        # Extract price/MRP
        price = self._first_non_empty([
            soup.find("span", {"class": "a-price-whole"}).get_text(strip=True) if soup.find("span", {"class": "a-price-whole"}) else None,
            soup.find("span", {"id": "priceblock_ourprice"}).get_text(strip=True) if soup.find("span", {"id": "priceblock_ourprice"}) else None,
            soup.find("span", {"id": "priceblock_dealprice"}).get_text(strip=True) if soup.find("span", {"id": "priceblock_dealprice"}) else None,
        ])

        # Extract MRP (original price)
        mrp = self._first_non_empty([
            soup.find("span", {"class": "a-text-price"}).get_text(strip=True) if soup.find("span", {"class": "a-text-price"}) else None,
            soup.find("span", {"data-a-strike": "true"}).get_text(strip=True) if soup.find("span", {"data-a-strike": "true"}) else None,
        ])

        # Extract product features (bullet points) - Critical for compliance info
        features = []
        feature_bullets = soup.find("div", {"id": "feature-bullets"})
        if feature_bullets:
            for li in feature_bullets.find_all("li"):
                text = li.get_text(" ", strip=True)
                if text and len(text) > 5:  # Filter empty bullets
                    features.append(text)
        
        # Also check for featurebullets_feature_div
        alt_features = soup.find("div", {"id": "featurebullets_feature_div"})
        if alt_features:
            for li in alt_features.find_all("li"):
                text = li.get_text(" ", strip=True)
                if text and len(text) > 5 and text not in features:
                    features.append(text)
        
        logger.info(f"Amazon features extracted: {len(features)} items")

        # Extract specifications from multiple table sources
        specs: dict[str, str] = {}

        def clean_spec_value(value: str) -> str:
            """Clean specification value by removing duplicates and extra whitespace."""
            value = value.replace("\u200e", "").replace("\u200f", "")
            value = re.sub(r'\s+', ' ', value).strip()
            # Remove duplicate content pattern (e.g., "Value: Key: Value")
            if ": " in value:
                parts = value.split(": ")
                if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                    return parts[0].strip()
            return value

        def add_spec(key: str, value: str):
            """Add specification if valid and not duplicate."""
            key = key.replace("\u200e", "").replace("\u200f", "").replace(":", "").strip()
            value = clean_spec_value(value)
            # Skip empty, too short, or malformed entries
            if not key or not value or len(key) < 2 or len(value) < 1:
                return
            # Skip if key contains excessive whitespace (malformed)
            if "\n" in key or len(key) > 100:
                return
            # Skip duplicate keys
            if key in specs:
                return
            specs[key] = value

        # Product Details table (contains manufacturer, weight, dimensions, etc.)
        product_details = soup.find("div", {"id": "productDetails_detailBullets_sections1"})
        if product_details:
            for row in product_details.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    key = th.get_text(" ", strip=True)
                    value = td.get_text(" ", strip=True)
                    add_spec(key, value)

        # Technical Details table
        tech_details = soup.find("table", {"id": "productDetails_techSpec_section_1"})
        if tech_details:
            for row in tech_details.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    key = th.get_text(" ", strip=True)
                    value = td.get_text(" ", strip=True)
                    add_spec(key, value)

        # Additional Information section (food products have FSSAI here)
        add_info_section = soup.find("div", {"id": "productDetails_db_sections"})
        if add_info_section:
            for table in add_info_section.find_all("table"):
                for row in table.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(" ", strip=True)
                        value = td.get_text(" ", strip=True)
                        add_spec(key, value)

        # Detail bullets (alternative format used in some pages)
        detail_bullets = soup.find("div", {"id": "detailBullets_feature_div"})
        if detail_bullets:
            for li in detail_bullets.find_all("li"):
                spans = li.find_all("span", {"class": "a-list-item"})
                if not spans:
                    spans = li.find_all("span")
                for span in spans:
                    text = span.get_text(" ", strip=True)
                    if ":" in text and "\n" not in text:
                        parts = text.split(":", 1)
                        if len(parts) == 2:
                            add_spec(parts[0], parts[1])

        # Product overview boxes (some products use this format)
        overview_table = soup.find("table", {"class": "a-normal a-spacing-micro"})
        if overview_table:
            for row in overview_table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(" ", strip=True)
                    value = cells[1].get_text(" ", strip=True)
                    add_spec(key, value)

        # Product Information section (critical for food/cosmetics compliance)
        prod_info_div = soup.find("div", {"id": "prodDetails"})
        if prod_info_div:
            for table in prod_info_div.find_all("table"):
                for row in table.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(" ", strip=True)
                        value = td.get_text(" ", strip=True)
                        add_spec(key, value)

        # Important Information section (contains allergen info, ingredients for food)
        important_info = soup.find("div", {"id": "important-information"})
        important_text = ""
        if important_info:
            important_text = important_info.get_text("\n", strip=True)
            # Try to extract structured data from important info
            current_key = None
            for elem in important_info.find_all(["h4", "h5", "b", "strong", "p", "div"]):
                if elem.name in ["h4", "h5", "b", "strong"]:
                    current_key = elem.get_text(strip=True).replace(":", "").strip()
                elif current_key and elem.name in ["p", "div"]:
                    value = elem.get_text(" ", strip=True)
                    if value and len(value) > 3:
                        add_spec(current_key, value)
                        current_key = None

        # A-plus content / Enhanced brand content
        aplus_content = ""
        aplus_div = soup.find("div", {"id": "aplus"})
        if aplus_div:
            aplus_content = aplus_div.get_text("\n", strip=True)

        # Product description
        description = self._first_non_empty([
            soup.find("div", {"id": "productDescription"}).get_text(" ", strip=True) if soup.find("div", {"id": "productDescription"}) else None,
            soup.find("meta", attrs={"name": "description"}).get("content") if soup.find("meta", attrs={"name": "description"}) else None,
            soup.find("meta", property="og:description").get("content") if soup.find("meta", property="og:description") else None,
        ])

        # Extract FSSAI License from page text (critical for food compliance)
        page_text = soup.get_text(" ", strip=True)
        fssai_patterns = [
            r'FSSAI\s*(?:License|Lic\.?|No\.?|Number)?[:\s]*(\d{14})',
            r'FSSAI[:\s]*(\d{14})',
            r'License\s*No\.?[:\s]*(\d{14})',
            r'Lic\.?\s*No\.?[:\s]*(\d{14})',
        ]
        for pattern in fssai_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                add_spec("FSSAI License Number", match.group(1))
                break

        # Extract other food compliance fields from text
        if "FSSAI License Number" not in specs:
            # Check in important info specifically
            if important_text:
                fssai_match = re.search(r'(\d{14})', important_text)
                if fssai_match:
                    add_spec("FSSAI License Number", fssai_match.group(1))

        logger.info(f"Amazon specs extracted: {len(specs)} items")
        
        # Extract ALL product images comprehensively
        image_urls: list[str] = []
        seen_urls: set[str] = set()
        
        def add_image(src: str, convert_thumbnail: bool = False):
            """Add image URL if valid and not duplicate."""
            if not src or not isinstance(src, str):
                return
            # Handle dynamic image JSON format
            if src.startswith("{"):
                try:
                    import json
                    img_dict = json.loads(src)
                    if img_dict:
                        # Get highest resolution image
                        src = max(img_dict.keys(), key=lambda x: img_dict.get(x, [0, 0])[0] * img_dict.get(x, [0, 0])[1])
                except:
                    return
            # Convert thumbnail to full size URL if requested
            if convert_thumbnail:
                src = re.sub(r'\._[A-Z0-9_]+_\.', '.', src)
            # Skip sprites, transparent pixels, icons
            skip_patterns = ["sprite", "transparent", "1x1", "blank", "icon", "logo", "loading"]
            if any(p in src.lower() for p in skip_patterns):
                return
            resolved = urljoin(url, src)
            # Normalize URL for deduplication
            normalized = re.sub(r'\._[A-Z0-9_]+_\.', '.', resolved)
            if resolved.startswith("http") and normalized not in seen_urls:
                seen_urls.add(normalized)
                image_urls.append(resolved)
        
        # 1. Main landing image (highest priority)
        main_img = soup.find("img", {"id": "landingImage"})
        if main_img:
            add_image(main_img.get("data-old-hires"))
            add_image(main_img.get("data-a-dynamic-image"))
            add_image(main_img.get("src"))

        # 2. Image gallery / alternate images
        thumb_container = soup.find("div", {"id": "altImages"})
        if thumb_container:
            for img in thumb_container.find_all("img"):
                add_image(img.get("src"), convert_thumbnail=True)
                add_image(img.get("data-old-hires"))
        
        # 3. Image block container (another gallery location)
        image_block = soup.find("div", {"id": "imageBlock"})
        if image_block:
            for img in image_block.find_all("img"):
                add_image(img.get("src"), convert_thumbnail=True)
                add_image(img.get("data-old-hires"))
        
        # 4. A+ content / Enhanced Brand Content images
        aplus_div = soup.find("div", {"id": "aplus"})
        if aplus_div:
            for img in aplus_div.find_all("img"):
                add_image(img.get("src"))
                add_image(img.get("data-src"))
        
        # 5. Product description images
        desc_div = soup.find("div", {"id": "productDescription"})
        if desc_div:
            for img in desc_div.find_all("img"):
                add_image(img.get("src"))
        
        # 6. Important information images
        important_div = soup.find("div", {"id": "important-information"})
        if important_div:
            for img in important_div.find_all("img"):
                add_image(img.get("src"))
        
        # 7. Rich product description (newer Amazon layout)
        rich_desc = soup.find("div", {"id": "richProductDescription"})
        if rich_desc:
            for img in rich_desc.find_all("img"):
                add_image(img.get("src"))
        
        # 8. Feature bullets area images
        feature_div = soup.find("div", {"id": "feature-bullets"})
        if feature_div:
            for img in feature_div.find_all("img"):
                add_image(img.get("src"))
        
        # 9. Product overview images
        overview = soup.find("div", {"id": "productOverview_feature_div"})
        if overview:
            for img in overview.find_all("img"):
                add_image(img.get("src"))
        
        # 10. Extract images from data attributes (JavaScript-loaded galleries)
        for script in soup.find_all("script", type="text/javascript"):
            script_text = script.string or ""
            # Look for high-res image URLs in JavaScript
            hiRes_matches = re.findall(r'"hiRes"\s*:\s*"(https?://[^"]+)"', script_text)
            for match in hiRes_matches:
                add_image(match)
            large_matches = re.findall(r'"large"\s*:\s*"(https?://[^"]+)"', script_text)
            for match in large_matches:
                add_image(match)
        
        logger.info(f"Amazon images extracted: {len(image_urls)} URLs")

        # Build comprehensive raw text - extract EVERYTHING from the page
        raw_parts = [
            f"Title: {title}" if title else "",
            f"Price: {price}" if price else "",
            f"MRP: {mrp}" if mrp else "",
        ]
        
        # Features
        if features:
            raw_parts.append("Features:")
            raw_parts.extend(f"- {f}" for f in features)
        
        # All specifications
        if specs:
            raw_parts.append("\nProduct Specifications:")
            raw_parts.extend(f"{k}: {v}" for k, v in specs.items())
        
        # Description
        if description:
            raw_parts.append("\nDescription:")
            raw_parts.append(description)
        
        # Important Information (full text)
        if important_text:
            raw_parts.append("\nImportant Information:")
            raw_parts.append(important_text)
        
        # A+ content (full text)
        if aplus_content:
            raw_parts.append("\nA+ Content / Enhanced Brand Content:")
            raw_parts.append(aplus_content)
        
        # Extract comprehensive text from key page sections
        section_ids = [
            "productTitle", "titleSection", "centerCol", "leftCol", "rightCol",
            "dp-container", "productDescription", "productDetails_feature_div",
            "detailBulletsWrapper_feature_div", "technical-data", "product-facts",
            "featurebullets_feature_div", "btfContent", "brand-story-widget"
        ]
        for section_id in section_ids:
            section = soup.find(id=section_id)
            if section:
                section_text = section.get_text(" ", strip=True)
                if section_text and len(section_text) > 50:
                    # Avoid duplicating content already captured
                    if section_text not in raw_parts:
                        raw_parts.append(f"\n[Section {section_id}]:")
                        raw_parts.append(section_text[:5000])  # Limit per section
        
        # Full page text as fallback (last 10000 chars to avoid oversized output)
        full_page_text = soup.get_text(" ", strip=True)
        raw_parts.append("\n[Full Page Text Extract]:")
        raw_parts.append(full_page_text[:10000])
        
        raw_text = "\n".join(part for part in raw_parts if part)

        # Add additional fields to specs
        if price:
            specs["Selling Price"] = price
        if mrp:
            specs["MRP"] = mrp

        return ScrapedProductData(
            url=url,
            title=title or None,
            description=description or None,
            specifications=specs,
            image_urls=image_urls,  # All images, no limit
            raw_text=raw_text,
        )

    def _extract_flipkart_data(self, soup: BeautifulSoup, url: str) -> ScrapedProductData:
        """Extract product data from Flipkart product pages."""
        
        # Extract title
        title = self._first_non_empty([
            soup.find("span", {"class": "VU-ZEz"}).get_text(strip=True) if soup.find("span", {"class": "VU-ZEz"}) else None,
            soup.find("span", {"class": "B_NuCI"}).get_text(strip=True) if soup.find("span", {"class": "B_NuCI"}) else None,
            soup.find("h1", {"class": "_6EBuvT"}).get_text(strip=True) if soup.find("h1", {"class": "_6EBuvT"}) else None,
            soup.find("meta", property="og:title").get("content") if soup.find("meta", property="og:title") else None,
        ])

        # Extract price
        price = self._first_non_empty([
            soup.find("div", {"class": "Nx9bqj CxhGGd"}).get_text(strip=True) if soup.find("div", {"class": "Nx9bqj CxhGGd"}) else None,
            soup.find("div", {"class": "_30jeq3 _16Jk6d"}).get_text(strip=True) if soup.find("div", {"class": "_30jeq3 _16Jk6d"}) else None,
        ])

        # Extract MRP
        mrp = self._first_non_empty([
            soup.find("div", {"class": "yRaY8j A6+E6v"}).get_text(strip=True) if soup.find("div", {"class": "yRaY8j A6+E6v"}) else None,
            soup.find("div", {"class": "_3I9_wc _2p6lqe"}).get_text(strip=True) if soup.find("div", {"class": "_3I9_wc _2p6lqe"}) else None,
        ])

        specs: dict[str, str] = {}

        # Product highlights
        highlights = soup.find("div", {"class": "_1AN87F"})
        if highlights:
            for li in highlights.find_all("li"):
                text = li.get_text(" ", strip=True)
                if ":" in text:
                    key, value = text.split(":", 1)
                    specs[key.strip()] = value.strip()

        # Specifications table
        spec_tables = soup.find_all("div", {"class": "_4BJ2V+"})
        if not spec_tables:
            spec_tables = soup.find_all("div", {"class": "_14cfVK"})
        
        for spec_div in spec_tables:
            rows = spec_div.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(" ", strip=True)
                    value = cells[1].get_text(" ", strip=True)
                    if key and value:
                        specs[key] = value

        # Description
        description = self._first_non_empty([
            soup.find("div", {"class": "_1mXcCf RmoJUa"}).get_text(" ", strip=True) if soup.find("div", {"class": "_1mXcCf RmoJUa"}) else None,
            soup.find("meta", attrs={"name": "description"}).get("content") if soup.find("meta", attrs={"name": "description"}) else None,
        ])

        # Extract ALL images comprehensively
        image_urls: list[str] = []
        seen_urls: set[str] = set()
        
        def add_flipkart_image(src: str):
            if not src or not src.startswith("http"):
                return
            # Skip placeholder/loading images
            if "loading" in src.lower() or "placeholder" in src.lower():
                return
            # Convert to high resolution
            full_src = re.sub(r'/\d+/\d+/', '/832/832/', src)
            if full_src not in seen_urls:
                seen_urls.add(full_src)
                image_urls.append(full_src)
        
        # Product gallery images
        for img in soup.find_all("img", {"class": "_396cs4"}):
            add_flipkart_image(img.get("src"))
        
        # Thumbnail images
        for img in soup.find_all("img", {"class": "_2amPTt _3nMsss"}):
            add_flipkart_image(img.get("src"))
        
        # All product images in the image slider
        for img in soup.find_all("img", {"class": re.compile(r"_\w+\s*_\w+")}):
            src = img.get("src") or img.get("data-src")
            if src and ("flipkart" in src or "f1commerce" in src):
                add_flipkart_image(src)
        
        # Images from product description
        desc_container = soup.find("div", {"class": re.compile(r"(RmoJUa|_1mXcCf)")})
        if desc_container:
            for img in desc_container.find_all("img"):
                add_flipkart_image(img.get("src"))

        if price:
            specs["Selling Price"] = price
        if mrp:
            specs["MRP"] = mrp

        # Comprehensive raw text
        raw_text = "\n".join(chunk.strip() for chunk in soup.stripped_strings if chunk and chunk.strip())

        return ScrapedProductData(
            url=url,
            title=title or None,
            description=description or None,
            specifications=specs,
            image_urls=image_urls,  # All images, no limit
            raw_text=raw_text,
        )

    def _extract_generic_data(self, soup: BeautifulSoup, url: str) -> ScrapedProductData:
        """Extract product data from generic e-commerce pages."""
        
        title = self._first_non_empty([
            soup.find("meta", property="og:title").get("content") if soup.find("meta", property="og:title") else None,
            soup.find("meta", attrs={"name": "twitter:title"}).get("content") if soup.find("meta", attrs={"name": "twitter:title"}) else None,
            soup.title.text if soup.title else None,
            soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else None,
        ])

        description = self._first_non_empty([
            soup.find("meta", attrs={"name": "description"}).get("content") if soup.find("meta", attrs={"name": "description"}) else None,
            soup.find("meta", property="og:description").get("content") if soup.find("meta", property="og:description") else None,
            soup.find("p").get_text(" ", strip=True) if soup.find("p") else None,
        ])

        specs: dict[str, str] = {}
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].get_text(" ", strip=True)
                    value = cells[1].get_text(" ", strip=True)
                    if key and value and key not in specs:
                        specs[key] = value

        for item in soup.find_all("li"):
            text = item.get_text(" ", strip=True)
            if ":" in text:
                key, value = text.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key and value and key not in specs:
                    specs[key] = value

        image_urls: list[str] = []
        for image in soup.find_all("img"):
            src = image.get("src") or image.get("data-src") or image.get("data-original")
            if not src:
                continue
            resolved = urljoin(url, src)
            if resolved.startswith("http") and resolved not in image_urls:
                image_urls.append(resolved)

        raw_text = "\n".join(chunk.strip() for chunk in soup.stripped_strings if chunk and chunk.strip())

        return ScrapedProductData(
            url=url,
            title=title or None,
            description=description or None,
            specifications=specs,
            image_urls=image_urls,
            raw_text=raw_text,
        )

    def fetch_product_data(self, url: str) -> ScrapedProductData:
        """Fetch and extract product data from e-commerce URL."""
        try:
            response = self.session.get(url, timeout=30)
        except request_exceptions.SSLError:
            response = self.session.get(url, timeout=30, verify=False)
        response.raise_for_status()

        # Log response status
        logger.info(f"Fetched URL: {url}, Status: {response.status_code}, Length: {len(response.text)}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Route to appropriate parser based on URL
        if self._is_amazon_url(url):
            logger.info("Using Amazon-specific parser")
            return self._extract_amazon_data(soup, url)
        elif self._is_flipkart_url(url):
            logger.info("Using Flipkart-specific parser")
            return self._extract_flipkart_data(soup, url)
        else:
            logger.info("Using generic parser")
            return self._extract_generic_data(soup, url)
