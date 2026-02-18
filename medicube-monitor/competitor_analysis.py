#!/usr/bin/env python3
"""
Competitor price analysis for Medicube products.
Scrapes all accessible competitor stores, compares prices with eonni.com.ua,
and sends a detailed report to Telegram.
"""

import re
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'uk-UA,uk;q=0.9,en;q=0.8',
}

TOKEN = "8450762615:AAF0j3A0bRhA0zejgLEZgma4t8nAvBtF2bg"
CHAT_ID = "300367602"
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_tg(text: str):
    """Send message to Telegram with retry."""
    for attempt in range(3):
        try:
            r = requests.post(API, json={
                "chat_id": CHAT_ID, "text": text,
                "parse_mode": "HTML", "disable_web_page_preview": True,
            }, timeout=15)
            d = r.json()
            if d.get("ok"):
                return True
            if r.status_code == 429:
                wait = d.get("parameters", {}).get("retry_after", 5) + 1
                time.sleep(wait)
            else:
                logger.error(f"TG send failed: {d}")
                return False
        except Exception as e:
            logger.error(f"TG error: {e}")
    return False


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_price(text: str) -> Optional[int]:
    """Extract numeric price in UAH from text."""
    if not text:
        return None
    text = text.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u00a0', ' ')
    # "1 299 грн", "799₴", "₴1299", "1299.00 грн"
    m = re.search(r'([\d][\d\s]*(?:[.,]\d{1,2})?)\s*(?:₴|грн|UAH|uah)', text, re.I)
    if m:
        return int(re.sub(r'[\s.,]', '', m.group(1).split(',')[0].split('.')[0]))
    m = re.search(r'(?:₴|грн|UAH)\s*([\d][\d\s]*)', text, re.I)
    if m:
        return int(re.sub(r'\s', '', m.group(1)))
    # Just digits > 50 (probably price)
    m = re.search(r'\b(\d[\d\s]{1,8})\b', text)
    if m:
        val = int(re.sub(r'\s', '', m.group(1)))
        if 50 < val < 50000:
            return val
    return None


# Normalize product name for matching
def normalize_name(name: str) -> str:
    """Normalize product name for cross-store matching."""
    n = name.lower().strip()
    n = re.sub(r'\s+', ' ', n)
    # Remove common prefixes/suffixes
    n = re.sub(r'^medicube\s+', '', n)
    n = re.sub(r'^메디큐브\s+', '', n)
    n = re.sub(r'\s*\d+\s*ml\b', '', n)
    n = re.sub(r'\s*\d+\s*г\b', '', n)
    n = re.sub(r'\s*\d+\s*мл\b', '', n)
    n = re.sub(r'[^\w\s]', '', n)
    n = n.strip()
    return n


# ==================== STORE SCRAPERS ====================

def scrape_eonni() -> List[dict]:
    """Scrape eonni.com.ua via API."""
    logger.info("Scraping eonni.com.ua...")
    try:
        r = requests.get('https://eonni.com.ua/api/products', headers=H, timeout=15)
        data = r.json()
        products = []
        for p in data:
            brand = str(p.get('brand', '') or '')
            if brand.lower() not in ('medicube', 'age-r', ''):
                continue
            name = p.get('name', '')
            if not name:
                continue
            # Only include if it looks like a Medicube product
            if brand.lower() not in ('medicube',) and not any(kw in name.lower() for kw in ['pdrn', 'zero pore', 'collagen', 'red ', 'exosome', 'deep vita', 'age-r', 'ager']):
                continue
            price = p.get('sale_price') or p.get('original_price')
            stock = p.get('stock_quantity', 0) or 0
            products.append({
                'name': name,
                'price': int(price) if price and int(price) > 50 else None,
                'in_stock': stock > 0,
                'url': f"https://eonni.com.ua/product/{p.get('id', '')}",
            })
        logger.info(f"  eonni.com.ua: {len(products)} Medicube products")
        return products
    except Exception as e:
        logger.error(f"  eonni.com.ua error: {e}")
        return []


def scrape_beauty_systema() -> List[dict]:
    """Scrape beauty-systema.com for Medicube products."""
    logger.info("Scraping beauty-systema.com...")
    products = []
    try:
        for page in range(1, 6):
            url = f'https://www.beauty-systema.com/search?q=medicube&page={page}'
            r = requests.get(url, headers=H, timeout=15)
            s = BeautifulSoup(r.text, 'html.parser')
            cards = s.select('.product-card, .product-item, .grid-product, .productCard')
            if not cards:
                cards = s.select('[class*="product"]')
            found = 0
            for card in cards:
                name_el = card.select_one('a[href*="/product"], .product-card__title, .product__title, h3, .title')
                price_el = card.select_one('.price, [class*="price"], .money')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or 'medicube' not in name.lower() and 'pdrn' not in name.lower():
                    continue
                href = name_el.get('href', '')
                if not href:
                    link = card.select_one('a')
                    href = link.get('href', '') if link else ''
                price = None
                if price_el:
                    price = extract_price(price_el.get_text())
                in_stock = True
                stock_el = card.select_one('[class*="sold-out"], [class*="out-of-stock"]')
                if stock_el:
                    in_stock = False
                full_url = href if href.startswith('http') else f'https://www.beauty-systema.com{href}'
                products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
                found += 1
            if found == 0:
                break
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"  beauty-systema.com error: {e}")
    logger.info(f"  beauty-systema.com: {len(products)} products")
    return products


def _scrape_generic_search(domain: str, search_url: str, base_url: str = '') -> List[dict]:
    """Generic scraper for sites with search functionality."""
    if not base_url:
        base_url = f'https://{domain}'
    products = []
    try:
        r = requests.get(search_url, headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')

        # Strategy: find all product links with prices nearby
        # Look for product cards
        for sel in ['.product-card', '.product-item', '.product', '.goods-item',
                    '.catalog-item', '.product-layout', '.b-product-gallery__item',
                    '.product-thumb', '.product_item', '.collection-item',
                    'li[class*="product"]', 'div[class*="product"]']:
            cards = s.select(sel)
            if 2 <= len(cards) <= 200:
                for card in cards:
                    name_el = (card.select_one('.product-card__name, .product__name, .product-name, '
                                                '.product__title, .product-card__title, '
                                                'h3 a, h2 a, .name a, .title a, a.name, a.title')
                               or card.select_one('a'))
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)[:120]
                    if not name:
                        continue

                    # Get price
                    price_el = card.select_one('.price, [class*="price"]:not([class*="old"]):not([class*="compare"]), .money')
                    price = extract_price(price_el.get_text()) if price_el else None

                    # Get URL
                    href = name_el.get('href', '')
                    if not href:
                        link = card.select_one('a')
                        href = link.get('href', '') if link else ''
                    full_url = href if href.startswith('http') else f'{base_url}{href}'

                    # Stock
                    in_stock = True
                    card_text = card.get_text().lower()
                    if 'немає' in card_text or 'sold out' in card_text or 'відсутній' in card_text:
                        in_stock = False

                    products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
                if products:
                    break
    except Exception as e:
        logger.error(f"  {domain} error: {e}")
    return products


def scrape_sisters() -> List[dict]:
    """Scrape sisters.co.ua."""
    logger.info("Scraping sisters.co.ua...")
    products = []
    try:
        r = requests.get('https://sisters.co.ua/search/?search=medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-thumb, .product-layout, [class*="product"]')
        if not cards:
            # Try a different approach - find product links
            for a in s.select('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if ('medicube' in text.lower() or 'medicube' in href.lower()) and len(text) > 5:
                    parent = a.parent
                    price = None
                    if parent:
                        price_el = parent.select_one('.price, [class*="price"]')
                        if price_el:
                            price = extract_price(price_el.get_text())
                        if not price:
                            for sib in parent.find_next_siblings():
                                price_el = sib.select_one('.price, [class*="price"]')
                                if price_el:
                                    price = extract_price(price_el.get_text())
                                    break
                    full_url = href if href.startswith('http') else f'https://sisters.co.ua{href}'
                    products.append({'name': text[:120], 'price': price, 'in_stock': True, 'url': full_url})
        else:
            for card in cards:
                name_el = card.select_one('.name a, h4 a, .caption a, a[href*="product"]')
                price_el = card.select_one('.price-new, .price, [class*="price"]')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if 'medicube' not in name.lower() and 'pdrn' not in name.lower():
                    continue
                price = extract_price(price_el.get_text()) if price_el else None
                href = name_el.get('href', '')
                full_url = href if href.startswith('http') else f'https://sisters.co.ua{href}'
                in_stock = 'немає' not in card.get_text().lower()
                products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  sisters.co.ua error: {e}")
    logger.info(f"  sisters.co.ua: {len(products)} products")
    return products


def scrape_beautysmart() -> List[dict]:
    """Scrape beautysmart.com.ua."""
    logger.info("Scraping beautysmart.com.ua...")
    products = []
    try:
        for page in range(1, 4):
            url = f'https://beautysmart.com.ua/brendy/medicube/?page={page}'
            r = requests.get(url, headers=H, timeout=15)
            s = BeautifulSoup(r.text, 'html.parser')
            cards = s.select('.product-card, .catalog-item, .product-item, .product-layout, [class*="product"]')
            if not cards:
                # Try finding by links
                for a in s.select('a[href*="/medicube"], a[href*="medicube"]'):
                    text = a.get_text(strip=True)
                    if len(text) > 10 and len(text) < 200:
                        parent = a.parent
                        price = None
                        for p_el in (parent.select('[class*="price"]') if parent else []):
                            price = extract_price(p_el.get_text())
                            if price:
                                break
                        href = a.get('href', '')
                        full_url = href if href.startswith('http') else f'https://beautysmart.com.ua{href}'
                        in_stock = True
                        if parent:
                            pt = parent.get_text().lower()
                            if 'немає' in pt or 'відсутній' in pt:
                                in_stock = False
                        products.append({'name': text, 'price': price, 'in_stock': in_stock, 'url': full_url})
            else:
                found = 0
                for card in cards:
                    name_el = card.select_one('.product-card__name, .product__title, h3, a[href*="medicube"]')
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if not name:
                        continue
                    price_el = card.select_one('.price:not(.price--old), [class*="price"]:not([class*="old"])')
                    price = extract_price(price_el.get_text()) if price_el else None
                    href = name_el.get('href', '') or (card.select_one('a') or {}).get('href', '')
                    full_url = href if href.startswith('http') else f'https://beautysmart.com.ua{href}'
                    in_stock = 'немає' not in card.get_text().lower()
                    products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
                    found += 1
                if found == 0:
                    break
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"  beautysmart.com.ua error: {e}")
    logger.info(f"  beautysmart.com.ua: {len(products)} products")
    return products


def scrape_lullaby() -> List[dict]:
    """Scrape lullaby.ua."""
    logger.info("Scraping lullaby.ua...")
    products = []
    try:
        r = requests.get('https://lullaby.ua/brands/medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-card, .catalog-item, .product-item, .product, .product-thumb')
        if not cards:
            cards = s.select('[class*="ProductCard"], [class*="product-card"], [class*="product_card"]')
        if not cards:
            # Fallback: search all links
            for a in s.select('a[href]'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if ('/product/' in href or '/tovar/' in href) and len(text) > 10:
                    parent = a.parent
                    if parent:
                        ptext = parent.get_text()
                        price = extract_price(ptext)
                    else:
                        price = None
                    full_url = href if href.startswith('http') else f'https://lullaby.ua{href}'
                    products.append({'name': text[:120], 'price': price, 'in_stock': True, 'url': full_url})
        else:
            for card in cards:
                name_el = card.select_one('.product-card__title, .product__title, h3, .name, .title, a')
                price_el = card.select_one('.product-card__price, .price, [class*="price"]')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                price = extract_price(price_el.get_text()) if price_el else None
                href = name_el.get('href', '') or (card.select_one('a') or {}).get('href', '')
                full_url = href if href.startswith('http') else f'https://lullaby.ua{href}'
                in_stock = 'немає' not in card.get_text().lower() and 'sold' not in card.get_text().lower()
                products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  lullaby.ua error: {e}")
    logger.info(f"  lullaby.ua: {len(products)} products")
    return products


def scrape_kylkalyaba() -> List[dict]:
    """Scrape kylkalyaba.com.ua."""
    logger.info("Scraping kylkalyaba.com.ua...")
    products = []
    try:
        r = requests.get('https://www.kylkalyaba.com.ua/ua/search/?search=medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-thumb, .product-layout, .product-item, [class*="product"]')
        for card in cards:
            name_el = card.select_one('.name a, .caption a, h4 a, .product-name a, a[href*="medicube"]')
            price_el = card.select_one('.price-new, .price, [class*="price"]:not([class*="old"])')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            price = extract_price(price_el.get_text()) if price_el else None
            href = name_el.get('href', '')
            full_url = href if href.startswith('http') else f'https://www.kylkalyaba.com.ua{href}'
            in_stock = 'немає' not in card.get_text().lower() and 'відсутній' not in card.get_text().lower()
            products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  kylkalyaba.com.ua error: {e}")
    logger.info(f"  kylkalyaba.com.ua: {len(products)} products")
    return products


def scrape_isei() -> List[dict]:
    """Scrape isei.ua."""
    logger.info("Scraping isei.ua...")
    products = []
    try:
        r = requests.get('https://isei.ua/ua/search?q=medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-card, .product-item, .catalog-item, [class*="product"]')
        for card in cards:
            name_el = card.select_one('.product-card__name, .product__name, h3 a, .name a, a')
            price_el = card.select_one('.product-card__price, .price, [class*="price"]:not([class*="old"])')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)[:150]
            if not name or len(name) < 5:
                continue
            price = extract_price(price_el.get_text()) if price_el else None
            href = name_el.get('href', '') or (card.select_one('a') or {}).get('href', '')
            full_url = href if href.startswith('http') else f'https://isei.ua{href}'
            in_stock = 'немає' not in card.get_text().lower()
            products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  isei.ua error: {e}")
    logger.info(f"  isei.ua: {len(products)} products")
    return products


def scrape_hitomi() -> List[dict]:
    """Scrape hitomi.com.ua."""
    logger.info("Scraping hitomi.com.ua...")
    products = []
    try:
        for page in range(1, 4):
            url = f'https://hitomi.com.ua/brand/medicube/?page={page}'
            r = requests.get(url, headers=H, timeout=15)
            s = BeautifulSoup(r.text, 'html.parser')
            cards = s.select('.product-card, .product-item, .product-thumb, .product-layout, [class*="product"]')
            found = 0
            for card in cards:
                name_el = card.select_one('.product-card__title, .product__title, h3 a, .name a, a[href*="/product/"]')
                price_el = card.select_one('.product-card__price, .price, [class*="price"]:not([class*="old"])')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)[:150]
                if not name or len(name) < 5:
                    continue
                price = extract_price(price_el.get_text()) if price_el else None
                href = name_el.get('href', '') or (card.select_one('a') or {}).get('href', '')
                full_url = href if href.startswith('http') else f'https://hitomi.com.ua{href}'
                in_stock = 'немає' not in card.get_text().lower()
                products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
                found += 1
            if found == 0:
                break
            time.sleep(0.5)
    except Exception as e:
        logger.error(f"  hitomi.com.ua error: {e}")
    logger.info(f"  hitomi.com.ua: {len(products)} products")
    return products


def scrape_koreanstory() -> List[dict]:
    """Scrape koreanstory.com.ua."""
    logger.info("Scraping koreanstory.com.ua...")
    products = []
    try:
        r = requests.get('https://koreanstory.com.ua/search/?search=medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-thumb, .product-layout, [class*="product-item"]')
        for card in cards:
            name_el = card.select_one('.name a, .caption a, h4 a, .product-name a')
            price_el = card.select_one('.price-new, .price, [class*="price"]:not([class*="old"])')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            price = extract_price(price_el.get_text()) if price_el else None
            href = name_el.get('href', '')
            full_url = href if href.startswith('http') else f'https://koreanstory.com.ua{href}'
            in_stock = True
            card_text = card.get_text().lower()
            if 'немає' in card_text or 'відсутній' in card_text or 'нет в наличии' in card_text:
                in_stock = False
            products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  koreanstory.com.ua error: {e}")
    logger.info(f"  koreanstory.com.ua: {len(products)} products")
    return products


def scrape_shine_bright() -> List[dict]:
    """Scrape shine-bright.com.ua."""
    logger.info("Scraping shine-bright.com.ua...")
    products = []
    try:
        r = requests.get('https://shine-bright.com.ua/ua/medicube', headers=H, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        cards = s.select('.product-card, .product-item, .product, [class*="product"]')
        for card in cards:
            name_el = card.select_one('.product-card__name, .product__title, h3, .name, .title, a[href*="/product"]')
            price_el = card.select_one('.product-card__price, .price, [class*="price"]:not([class*="old"])')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)[:150]
            if not name or len(name) < 5:
                continue
            price = extract_price(price_el.get_text()) if price_el else None
            href = name_el.get('href', '') or (card.select_one('a') or {}).get('href', '')
            full_url = href if href.startswith('http') else f'https://shine-bright.com.ua{href}'
            in_stock = 'немає' not in card.get_text().lower()
            products.append({'name': name, 'price': price, 'in_stock': in_stock, 'url': full_url})
    except Exception as e:
        logger.error(f"  shine-bright.com.ua error: {e}")
    logger.info(f"  shine-bright.com.ua: {len(products)} products")
    return products


# ==================== MAIN ====================

def scrape_all_stores() -> Dict[str, List[dict]]:
    """Scrape all stores. Returns store_name -> [products]."""
    stores = {}

    stores['eonni.com.ua'] = scrape_eonni()
    time.sleep(1)
    stores['beauty-systema.com'] = scrape_beauty_systema()
    time.sleep(1)
    stores['sisters.co.ua'] = scrape_sisters()
    time.sleep(1)
    stores['beautysmart.com.ua'] = scrape_beautysmart()
    time.sleep(1)
    stores['lullaby.ua'] = scrape_lullaby()
    time.sleep(1)
    stores['kylkalyaba.com.ua'] = scrape_kylkalyaba()
    time.sleep(1)
    stores['isei.ua'] = scrape_isei()
    time.sleep(1)
    stores['hitomi.com.ua'] = scrape_hitomi()
    time.sleep(1)
    stores['koreanstory.com.ua'] = scrape_koreanstory()
    time.sleep(1)
    stores['shine-bright.com.ua'] = scrape_shine_bright()

    return stores


if __name__ == '__main__':
    stores = scrape_all_stores()
    for name, prods in stores.items():
        print(f'\n{name}: {len(prods)} products')
        for p in prods[:5]:
            print(f'  {p["name"][:60]:60s} | {"₴"+str(p["price"]) if p["price"] else "N/A":>10s} | {"✓" if p["in_stock"] else "✗"}')
