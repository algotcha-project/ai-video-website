"""
Medicube Korea product scraper.
Scrapes all product categories from m.themedicube.co.kr
"""

import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://m.themedicube.co.kr"

# All known product categories on the site
CATEGORIES = {
    # Top-level categories
    44: "PRODUCT (All)",
    51: "NEW",
    52: "BEST",
    # Line-based categories
    47: "RED LINE",
    57: "ZERO LINE",
    414: "SUPER CICA LINE",
    264: "BLUE LINE",
    307: "DEEP LINE",
    760: "PDRN 라인",
    # Product type categories
    441: "상품 유형별",
    442: "클렌징",
    444: "패드",
    445: "스킨/토너",
    446: "앰플/세럼",
    447: "크림",
    448: "선 케어",
    449: "메이크업",
    450: "마스크팩",
    451: "바디",
    452: "헤어",
    603: "디바이스",
    # Function-based categories
    454: "기능별",
    458: "탄력/미백",
    460: "민감/진정",
    466: "라인별",
    501: "에이지알",
    90: "SET",
    93: "TOOL",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; SM-G981B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class Product:
    """Represents a single product from Medicube."""

    def __init__(self, product_no: str, name: str, url: str, price: str = "",
                 image_url: str = "", category: str = ""):
        self.product_no = product_no
        self.name = name
        self.url = url
        self.price = price
        self.image_url = image_url
        self.category = category

    def to_dict(self) -> dict:
        return {
            "product_no": self.product_no,
            "name": self.name,
            "url": self.url,
            "price": self.price,
            "image_url": self.image_url,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(
            product_no=data["product_no"],
            name=data["name"],
            url=data["url"],
            price=data.get("price", ""),
            image_url=data.get("image_url", ""),
            category=data.get("category", ""),
        )

    def __repr__(self):
        return f"Product(#{self.product_no}: {self.name})"


def _parse_products_from_page(html: str, category_name: str = "") -> Dict[str, Product]:
    """Parse products from a Cafe24 product list page."""
    soup = BeautifulSoup(html, "html.parser")
    products = {}

    descriptions = soup.select(".description")
    for desc in descriptions:
        box = desc.parent
        if not box:
            continue

        # Find product link
        link_el = box.select_one(".thumbnail a[href*='product_no']")
        if not link_el:
            link_el = box.select_one("a[href*='product_no']")
        if not link_el:
            continue

        # Find product name
        name_el = desc.select_one(".name a")
        if not name_el:
            name_el = desc.select_one("a")
        if not name_el:
            continue

        href = link_el.get("href", "")
        name = name_el.get_text(strip=True)
        if not name:
            continue

        # Extract product_no from URL
        match = re.search(r"product_no=(\d+)", href)
        if not match:
            continue
        product_no = match.group(1)

        # Build full URL
        if href.startswith("/"):
            full_url = f"{BASE_URL}{href}"
        elif not href.startswith("http"):
            full_url = f"{BASE_URL}/{href}"
        else:
            full_url = href

        # Try to get price from Cafe24 listInfo structure
        price = ""
        # Priority: 일반 회원가 (member price) > 판매가 (sale price)
        list_items = desc.select(".listInfo li.xans-record-")
        for li in list_items:
            ptitle = li.select_one(".ptitle")
            if not ptitle:
                continue
            title_text = ptitle.get_text(strip=True)
            # Get the price span (not the title span)
            spans = li.select("span")
            for span in spans:
                if span.find_parent(class_="ptitle"):
                    continue  # Skip title spans
                span_text = span.get_text(strip=True)
                price_match = re.search(r"[\d,]+\s*원", span_text)
                if price_match and "line-through" not in span.get("style", ""):
                    if "회원가" in title_text:
                        price = price_match.group(0)
                        break  # Best price, stop
                    elif "판매가" in title_text and not price:
                        price = price_match.group(0)
            if "회원가" in (ptitle.get_text(strip=True) if ptitle else "") and price:
                break  # Got member price, no need to check more

        # Try to get image URL
        image_url = ""
        img_el = box.select_one(".thumbnail img")
        if img_el:
            image_url = img_el.get("src", "") or img_el.get("data-original", "")
            if image_url.startswith("//"):
                image_url = "https:" + image_url

        products[product_no] = Product(
            product_no=product_no,
            name=name,
            url=full_url,
            price=price,
            image_url=image_url,
            category=category_name,
        )

    return products


def scrape_category(cate_no: int, category_name: str = "",
                    max_pages: int = 5) -> Dict[str, Product]:
    """Scrape all products from a given category (with pagination)."""
    all_products = {}

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/product/list.html?cate_no={cate_no}&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch category {cate_no} page {page}: {e}")
            break

        page_products = _parse_products_from_page(resp.text, category_name)

        if not page_products:
            break  # No more products on this page

        # Check if we got new products (not just duplicates from page 1)
        new_count = sum(1 for pid in page_products if pid not in all_products)
        all_products.update(page_products)

        if new_count == 0:
            break  # No new products, stop paginating

        logger.debug(f"Category {cate_no} page {page}: {len(page_products)} products "
                      f"({new_count} new)")

        # Be respectful - small delay between pages
        if page < max_pages:
            time.sleep(0.5)

    return all_products


def scrape_all_products() -> Dict[str, Product]:
    """
    Scrape ALL products from all categories on Medicube Korea.
    Returns dict of product_no -> Product.
    """
    all_products: Dict[str, Product] = {}
    
    # Key categories that contain ALL products
    # Using a subset that covers everything without too much overlap
    key_categories = {
        51: "NEW",
        52: "BEST",
        441: "상품 유형별 (By Type)",
        454: "기능별 (By Function)",
        466: "라인별 (By Line)",
        501: "에이지알 (AGE-R)",
        760: "PDRN 라인",
    }

    for cate_no, cat_name in key_categories.items():
        logger.info(f"Scraping category: {cat_name} (cate_no={cate_no})...")
        try:
            cat_products = scrape_category(cate_no, cat_name)
            new_count = sum(1 for pid in cat_products if pid not in all_products)
            all_products.update(cat_products)
            logger.info(f"  -> {len(cat_products)} products ({new_count} new unique)")
        except Exception as e:
            logger.error(f"Error scraping category {cat_name}: {e}")

        # Delay between categories
        time.sleep(1)

    logger.info(f"Total unique products found: {len(all_products)}")
    return all_products


def scrape_product_detail(product_no: str) -> Optional[dict]:
    """Scrape additional details for a specific product (optional enrichment)."""
    url = f"{BASE_URL}/product/detail.html?product_no={product_no}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        detail = {"product_no": product_no, "url": url}

        # Get product name from detail page
        name_el = soup.select_one(".headingArea h2, .prd_detail_tit, h2.name")
        if name_el:
            detail["name"] = name_el.get_text(strip=True)

        return detail
    except Exception as e:
        logger.warning(f"Failed to get detail for product #{product_no}: {e}")
        return None
