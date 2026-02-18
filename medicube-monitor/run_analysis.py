#!/usr/bin/env python3
"""
One-time competitive price analysis for Medicube products.
Scrapes eonni.com.ua + all accessible competitor stores,
matches products, and sends a full report to Telegram.
"""

import re
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'uk-UA,uk;q=0.9',
}
TOKEN = "8450762615:AAF0j3A0bRhA0zejgLEZgma4t8nAvBtF2bg"
CHAT_ID = "300367602"
TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_tg(text):
    for _ in range(3):
        r = requests.post(TG_API, json={
            "chat_id": CHAT_ID, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True
        }, timeout=15)
        d = r.json()
        if d.get("ok"):
            return True
        if r.status_code == 429:
            time.sleep(d.get("parameters", {}).get("retry_after", 5) + 1)
        else:
            log.error(f"TG: {d}")
            return False
    return False


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_price_uah(text):
    """Extract integer UAH price from text."""
    if not text:
        return None
    text = text.replace('\xa0', ' ').replace('\u2009', ' ')
    # "1 350₴", "1350.00грн", "₴1350", "1 350 грн"
    m = re.search(r'(\d[\d\s]*(?:\.\d{1,2})?)\s*(?:₴|грн)', text)
    if m:
        num = re.sub(r'\s', '', m.group(1)).split('.')[0]
        val = int(num)
        if val > 30:
            return val
    m = re.search(r'(?:₴|грн)\s*(\d[\d\s]*)', text)
    if m:
        val = int(re.sub(r'\s', '', m.group(1)))
        if val > 30:
            return val
    return None


# =========== SCRAPERS ===========

def scrape_eonni():
    """eonni.com.ua - via REST API"""
    log.info("Scraping eonni.com.ua...")
    r = requests.get('https://eonni.com.ua/api/products', headers=H, timeout=15)
    data = r.json()
    products = []
    for p in data:
        brand = str(p.get('brand') or '')
        name = p.get('name', '')
        if not name:
            continue
        if brand.lower() != 'medicube' and not any(
            kw in name.lower() for kw in ['pdrn', 'zero pore', 'collagen', 'red ',
                'exosome', 'deep vita', 'age-r', 'triple collagen', 'succinic',
                'hyaluronic', 'peptide', 'cica', 'teatree', 'niacinamide']
        ):
            continue
        price_raw = p.get('sale_price') or p.get('original_price')
        price = int(float(price_raw)) if price_raw and float(price_raw) > 50 else None
        stock = (p.get('stock_quantity') or 0) > 0
        products.append({
            'name': name,
            'name_en': name,
            'price': price,
            'in_stock': stock,
            'url': f"https://eonni.com.ua/product/{p.get('id', '')}",
        })
    log.info(f"  eonni: {len(products)} products")
    return products


def scrape_lullaby():
    """lullaby.ua - via Next.js _next/data API"""
    log.info("Scraping lullaby.ua...")
    # First get buildId
    r = requests.get('https://lullaby.ua/brands/medicube', headers=H, timeout=15)
    s = BeautifulSoup(r.text, 'html.parser')
    build_id = None
    for sc in s.select('script[src*="_buildManifest"]'):
        m = re.search(r'/([^/]+)/_buildManifest', sc.get('src', ''))
        if m:
            build_id = m.group(1)
            break
    if not build_id:
        log.error("  lullaby: can't find buildId")
        return []

    all_products = []
    page = 1
    while True:
        url = f'https://lullaby.ua/_next/data/{build_id}/brands/medicube.json'
        if page > 1:
            url += f'?page={page}'
        r = requests.get(url, headers=H, timeout=15)
        if r.status_code != 200:
            break
        d = r.json()
        prods_data = d['pageProps']['initialState']['categories']['category']['products']
        items = prods_data.get('data', [])
        if not items:
            break
        for p in items:
            price_str = str(p.get('price', ''))
            price = int(float(price_str)) if price_str and float(price_str) > 30 else None
            qty = p.get('quantity', 0) or 0
            all_products.append({
                'name': p.get('title', ''),
                'name_en': p.get('title_en', ''),
                'price': price,
                'in_stock': qty > 0,
                'url': f"https://lullaby.ua{p.get('url', '')}",
            })
        total = prods_data.get('meta', {}).get('total', 0)
        if len(all_products) >= total:
            break
        page += 1
        time.sleep(0.5)

    log.info(f"  lullaby: {len(all_products)} products")
    return all_products


def scrape_shine_bright():
    """shine-bright.com.ua - JS-rendered, scrape individual product pages"""
    log.info("Scraping shine-bright.com.ua...")
    products = []
    # The brand page is JS-rendered, so scrape known product URLs
    # We'll rely on the fact that lullaby has the same products with English names
    # which we can use to find them on shine-bright
    # For now, just check if the brand page has any JSON data
    r = requests.get('https://shine-bright.com.ua/ua/medicube', headers=H, timeout=15)
    s = BeautifulSoup(r.text, 'html.parser')

    # Try to find product data in scripts (Nuxt/Vue SSR)
    for sc in s.select('script'):
        t = sc.get_text()
        if '"price"' in t and len(t) > 1000:
            import json as j
            # Try to find product arrays
            for match in re.finditer(r'"title"\s*:\s*"([^"]+)".*?"price"\s*:\s*(\d+)', t[:50000]):
                name, price = match.group(1), int(match.group(2))
                if price > 30:
                    products.append({
                        'name': name, 'name_en': '', 'price': price,
                        'in_stock': True, 'url': 'https://shine-bright.com.ua/ua/medicube',
                    })
            break

    log.info(f"  shine-bright: {len(products)} products")
    return products


def scrape_hitomi():
    """hitomi.com.ua - WooCommerce/WoodMart brand page"""
    log.info("Scraping hitomi.com.ua...")
    products = []
    r = requests.get('https://hitomi.com.ua/ru/brend/medicube-ru/', headers=H, timeout=15)
    s = BeautifulSoup(r.text, 'html.parser')

    # WoodMart theme: div.product-grid-item with links and prices
    container = s.select_one('.products')
    if not container:
        log.warning("  hitomi: no .products container found")
        return products

    for wp in container.find_all('div', recursive=False):
        classes = ' '.join(wp.get('class', []))
        if 'product' not in classes:
            continue

        link_el = wp.select_one('a[href*="/product/"]')
        if not link_el:
            continue
        href = link_el.get('href', '')

        # Get name from link's image alt or product title
        name = ''
        img = wp.select_one('img.attachment-woocommerce_thumbnail, img')
        if img:
            name = img.get('alt', '').strip()
        if not name:
            title_el = wp.select_one('.wd-entities-title, .product-title, h3, h2')
            if title_el:
                name = title_el.get_text(strip=True)
        if not name:
            name = link_el.get_text(strip=True)[:120]

        # Price: format "1,100грн." in <bdi> tags
        price = None
        # Try sale price first (ins > bdi), then regular
        ins_bdi = wp.select_one('.price ins bdi')
        if ins_bdi:
            pt = ins_bdi.get_text(strip=True)
            m = re.match(r'([\d,]+)', pt)
            if m:
                price = int(m.group(1).replace(',', ''))
        if not price:
            bdi = wp.select_one('.price bdi')
            if bdi and not bdi.find_parent('del'):
                pt = bdi.get_text(strip=True)
                m = re.match(r'([\d,]+)', pt)
                if m:
                    price = int(m.group(1).replace(',', ''))

        in_stock = 'instock' in classes

        if name and price and price > 30:
            products.append({
                'name': name, 'name_en': '', 'price': price,
                'in_stock': in_stock, 'url': href,
            })

    log.info(f"  hitomi: {len(products)} products")
    return products


def scrape_isei():
    """isei.ua - scrape known medicube product pages via LD+JSON"""
    log.info("Scraping isei.ua...")
    products = []
    # Known Medicube product URLs from the site (found via Google)
    known_slugs = [
        'kolagenova-nichna-maska-plivka-12272',
        'medicube-collagen-lifting-mask-12271',
        'medicube-pdrn-pink-niacinamide-whip-cleanser-12274',
        'medicube-zero-pore-pad-12270',
        'medicube-red-succinic-peeling-pad-12269',
        'medicube-deep-vita-c-capsule-cream-12273',
    ]
    for slug in known_slugs:
        url = f'https://isei.ua/ua/{slug}'
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code != 200:
                continue
            s = BeautifulSoup(r.text, 'html.parser')
            # Get from LD+JSON
            for sc in s.select('script[type="application/ld+json"]'):
                try:
                    d = json.loads(sc.get_text())
                    if d.get('@type') == 'Product':
                        name = d.get('name', '')
                        offers = d.get('offers', {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        price = None
                        p_str = str(offers.get('price', ''))
                        if p_str:
                            try:
                                price = int(float(p_str))
                            except:
                                pass
                        avail = offers.get('availability', '')
                        in_stock = 'InStock' in avail
                        if name:
                            products.append({
                                'name': name, 'name_en': '', 'price': price,
                                'in_stock': in_stock, 'url': url,
                            })
                        break
                except:
                    pass
            time.sleep(0.5)
        except:
            pass
    log.info(f"  isei: {len(products)} products")
    return products


def scrape_beautysmart():
    """beautysmart.com.ua - WooCommerce"""
    log.info("Scraping beautysmart.com.ua...")
    products = []
    # The user linked a specific product. Let's scrape from WC search
    r = requests.get('https://beautysmart.com.ua/?s=medicube&post_type=product', headers=H, timeout=15)
    s = BeautifulSoup(r.text, 'html.parser')

    # Find product links
    seen = set()
    for a in s.select('a[href*="medicube"]'):
        href = a.get('href', '')
        if '/product/' not in href and '-medicube' not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        # Scrape individual product page for price
        try:
            r2 = requests.get(href, headers=H, timeout=10)
            s2 = BeautifulSoup(r2.text, 'html.parser')
            title = s2.select_one('h1')
            price_el = s2.select_one('.price ins .amount, .price .amount, [itemprop="price"]')
            if title:
                name = title.get_text(strip=True)
                price = None
                if price_el:
                    price = extract_price_uah(price_el.get_text())
                    if not price:
                        content = price_el.get('content', '')
                        if content:
                            try:
                                price = int(float(content))
                            except:
                                pass
                in_stock = 'outofstock' not in ' '.join(s2.select_one('body').get('class', []))
                products.append({
                    'name': name, 'name_en': '', 'price': price,
                    'in_stock': in_stock, 'url': href,
                })
            time.sleep(0.5)
        except:
            pass
    log.info(f"  beautysmart: {len(products)} products")
    return products


# =========== MATCHING ===========

# Canonical English names for matching across stores
PRODUCT_ALIASES = {
    'pdrn pink niacinamide whip cleanser': ['pdrn whip cleanser', 'пінка з полінуклеотидами', 'очищающая пенка с полинуклеотидами та ніацинамідом', 'очищающая пенка с полинуклеотидами и ниацинамидом', 'очищувальна пінка з полінуклеотидами'],
    'pdrn pink niacinamide milky toner': ['milky toner', 'тонер-молочко з глутатіоном', 'осветляющая сыворотка с липосомальным глутатионом'],
    'pdrn pink collagen capsule cream': ['pink collagen capsule cream', 'рожевий колагеновий капсульний крем'],
    'pdrn pink collagen toning gel toner pad': ['toning gel toner pad', 'тонізувальні пади'],
    'pdrn pink tension up mask': ['tension up mask', 'маска для підтяжки'],
    'zero pore pad': ['zero pore pad 2.0', 'пілінг-педи для очищення і звуження пор', 'пилинг-пэды для очищения и сужения пор'],
    'red succinic peeling pad': ['succinic peeling pad', 'сукциновий пілінг пад'],
    'deep vita c capsule cream': ['vita c capsule cream', 'освітлюючий капсульний крем з вітаміном с', 'осветляющий капсульный крем с витамином с'],
    'collagen night wrapping mask': ['night wrapping mask', 'колагенова нічна маска', 'коллагеновая ночная маска'],
    'collagen lifting mask': ['lifting mask', 'ліфтинг-маска з колагеном', 'лифтинг-маска с коллагеном'],
    'deep vita a retinol serum': ['retinol serum', 'антивікова сироватка з ретинолом', 'антивозрастная сыворотка с ретинолом'],
    'exosome cica cream': ['cica cream', 'відновлювальний крем з екзосомами центели', 'восстанавливающий крем с экзосомами центеллы'],
    'zero pore serum 2.0': ['zero pore serum', 'сироватка для звуження пор'],
    'zero pore cream 2.0': ['zero pore cream', 'зволожувальний балансуючий крем'],
    'triple collagen serum': ['потрійний колаген сироватка', 'сыворотка с тройным коллагеном', 'сироватка з потрійним колагеном'],
    'triple collagen cream': ['потрійний колаген крем', 'легкий крем із колагеном'],
    'triple collagen toner': ['потрійний колаген тонер', 'тонер з потрійним колагеном'],
    'collagen jelly cream': ['желе крем з колагеном', 'зволожувальна сироватка з полінуклеотидами та колагеном'],
    'pdrn lip sleeping mask': ['маска для губ', 'ночная маска для губ'],
    'hyaluronic multi peptide serum': ['мультипептидна сироватка', 'мультипептидная сыворотка'],
    'deep lifting peptide eye cream': ['крем для контуру очей з пептидним', 'подтягивающий крем для кожи вокруг глаз'],
    'red foam cleanser': ['red foam', 'пенка с экстрактом мелиссы'],
    'one day exosome shot 7500': ['exosome shot 7500', 'інтенсивна сироватка з екзосомами'],
    'one day exosome shot 2000': ['exosome shot 2000', 'регенеруюча сироватка з полінуклеотидами'],
    'pdrn hydrating gel cleanser': ['hydrating gel cleanser', 'зволожувальний гель для вмивання'],
    'pdrn pink collagen bubble serum': ['bubble serum', 'бабл сироватка'],
    'pdrn pink collagen glow jelly mist serum': ['glow jelly mist', 'сироватка-міст з полінуклеотидами'],
    'collagen glow booster serum': ['glow booster serum', 'гель-бустер з полінуклеотидами'],
    'txa niacinamide 15 serum': ['niacinamide 15 serum', 'осветляющая сыворотка с транексамовой кислотой', 'освітлююча сироватка'],
    'txa niacinamide capsule cream': ['niacinamide capsule cream'],
    'zero foam cleanser': ['zero foam cleanser', 'пенка для глубокого очищения', 'пінка для глибокого очищення пор'],
    'zero pore blackhead deep cleansing oil': ['cleansing oil', 'гідрофільна олійка', 'гидрофильное масло'],
    'zero pore blackhead mud mask': ['mud mask', 'маска для видалення чорних крапок', 'охлаждающая маска для сужения пор'],
    'age-r booster pro': ['booster pro', 'пристрій для домашнього догляду', 'устройство для домашнего ухода'],
    'age-r booster pro mini': ['booster pro mini', 'міні-пристрій', 'мини-устройство'],
    'age-r booster pro case': ['booster pro case', 'захисний чохол', 'защитный чехол'],
    'deep vita c pad': ['vita c pad'],
    'deep vita c capsule serum': ['vita c capsule serum'],
    'red acne succinic acid peel': ['succinic acid peel'],
    'red clear capsule body lotion': ['body lotion'],
    'red acne body peeling shot': ['body peeling shot', 'протизапальний гель для душу', 'противовоспалительный гель для душа'],
    'pdrn pink peptide serum': ['pink peptide serum', 'відновлювальна сироватка з молекулами днк'],
    'pdrn pink peptide eye cream': ['pink peptide eye cream'],
    'pdrn collagen glow jelly serum': ['glow jelly serum'],
    'super cica daily quick mask': ['cica daily quick mask', 'щоденні маски для швидкого відновлення', 'ежедневные маски для быстрого восстановления'],
    'deep peptide radiance mask': ['peptide radiance mask'],
    'hyaluronic moisturising capsule cream': ['moisturising capsule cream'],
    'hyaluronic ceramide jelly cream': ['ceramide jelly cream'],
    'pdrn pink collagen exosome shot 2000': ['pink collagen exosome shot 2000'],
    'pdrn pink collagen exosome shot 7500': ['pink collagen exosome shot 7500'],
    'zero pore sa clear capsule cleansing foam': ['sa clear capsule', 'пінка для очищення пор'],
    'zero pore toner': ['пілінг-пади для чутливої шкіри'],
    'pdrn pink cica soothing toner': ['cica soothing toner', 'заспокійливий тонер з полінуклеотидами'],
    'pdrn pink collagen gel mask': ['collagen gel mask'],
    'exosome cica calming pad': ['cica calming pad', 'заспокійливий тонер з екзосомами центели'],
    'collagen milk tonning wrapping mask': ['milk tonning wrapping mask'],
    'age-r glutatione glow serum': ['glutatione glow serum'],
    'pdrn pink caffeine night wrapping mask': ['caffeine night wrapping mask'],
    'pdrn essence': ['pdrn essence'],
    'red succinic acid serum': ['succinic acid serum'],
    'collagen capsule patch retinol': ['capsule patch retinol'],
    'collagen capsule patch vitamin c': ['capsule patch vitamin c'],
    'deep vita c patch': ['vita c patch'],
}


def normalize(name):
    n = name.lower().strip()
    n = re.sub(r'\s+', ' ', n)
    n = re.sub(r'\d+\s*мл\b', '', n)
    n = re.sub(r'\d+\s*ml\b', '', n)
    n = re.sub(r'\d+\s*г\b', '', n)
    n = re.sub(r',\s*\d+.*$', '', n)
    n = re.sub(r'medicube\s*', '', n)
    n = re.sub(r'[^\w\s]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def match_product(name, eonni_products):
    """Match a competitor product name to an eonni product. Returns eonni product name or None."""
    name_norm = normalize(name)

    # Direct name match
    for ep in eonni_products:
        ep_norm = normalize(ep['name'])
        if ep_norm == name_norm:
            return ep['name']
        if SequenceMatcher(None, ep_norm, name_norm).ratio() > 0.85:
            return ep['name']

    # Match via aliases
    for canonical, aliases in PRODUCT_ALIASES.items():
        canonical_norm = normalize(canonical)
        is_match = False
        if canonical_norm in name_norm or name_norm in canonical_norm:
            is_match = True
        if not is_match:
            for alias in aliases:
                alias_norm = normalize(alias)
                if alias_norm in name_norm or name_norm in alias_norm:
                    is_match = True
                    break
                if SequenceMatcher(None, alias_norm, name_norm).ratio() > 0.7:
                    is_match = True
                    break
        if is_match:
            # Find matching eonni product
            for ep in eonni_products:
                ep_norm = normalize(ep['name'])
                if canonical_norm in ep_norm or ep_norm in canonical_norm:
                    return ep['name']
                if SequenceMatcher(None, canonical_norm, ep_norm).ratio() > 0.7:
                    return ep['name']
            return canonical.title()

    return None


# =========== MAIN ===========

def main():
    log.info("=" * 60)
    log.info("MEDICUBE COMPETITIVE PRICE ANALYSIS")
    log.info("=" * 60)

    # Step 1: Scrape all stores
    eonni = scrape_eonni()
    time.sleep(1)

    competitors = {}
    for name, func in [
        ('lullaby.ua', scrape_lullaby),
        ('shine-bright.com.ua', scrape_shine_bright),
        ('hitomi.com.ua', scrape_hitomi),
        ('isei.ua', scrape_isei),
        ('beautysmart.com.ua', scrape_beautysmart),
    ]:
        try:
            competitors[name] = func()
        except Exception as e:
            log.error(f"  {name} failed: {e}")
            competitors[name] = []
        time.sleep(1)

    # Step 2: Match products
    # Build a unified product table: product_name -> {store: {price, in_stock, url}}
    product_table = defaultdict(dict)

    # Add eonni products
    for p in eonni:
        product_table[p['name']]['eonni.com.ua'] = {
            'price': p['price'], 'in_stock': p['in_stock'], 'url': p['url']
        }

    # Match competitor products
    for store_name, store_products in competitors.items():
        for p in store_products:
            matched_name = match_product(p['name'], eonni)
            if matched_name:
                product_table[matched_name][store_name] = {
                    'price': p['price'], 'in_stock': p['in_stock'], 'url': p['url'],
                    'original_name': p['name'],
                }

    log.info(f"\nMatched {len(product_table)} products across stores")

    # Step 3: Build analysis
    send_tg("📊 <b>КОНКУРЕНТНИЙ АНАЛІЗ ЦІН — MEDICUBE</b>\n\n"
            f"🏪 Ваш магазин: eonni.com.ua\n"
            f"📦 Ваших товарів: {len(eonni)}\n"
            f"🏬 Конкурентів проаналізовано: {len(competitors)}\n"
            f"🔗 Співпадінь знайдено: {sum(1 for v in product_table.values() if len(v) > 1)}")
    time.sleep(1.5)

    # === PART 1: Prices per product per store ===
    send_tg("━" * 30 + "\n"
            "📋 <b>ЧАСТИНА 1: Ціни по магазинах</b>\n"
            "━" * 30)
    time.sleep(1.5)

    for product_name, stores in sorted(product_table.items()):
        if len(stores) < 2:
            continue  # Only show if product exists in at least eonni + 1 competitor

        lines = [f"📦 <b>{esc(product_name)}</b>\n"]
        for store, data in sorted(stores.items()):
            price = data.get('price')
            in_stock = data.get('in_stock', True)
            stock_icon = "✅" if in_stock else "❌"
            price_str = f"₴{price}" if price else "—"
            store_label = f"{'🏠' if store == 'eonni.com.ua' else '🏬'} {store}"
            lines.append(f"{store_label}: <b>{price_str}</b> {stock_icon}")

        send_tg("\n".join(lines))
        time.sleep(1.5)

    # === PART 2: Min/Max prices (only in-stock) ===
    send_tg("\n" + "━" * 30 + "\n"
            "📈 <b>ЧАСТИНА 2: Найнижча / Найвища ціна</b>\n"
            "(тільки товари в наявності)\n"
            "━" * 30)
    time.sleep(1.5)

    price_analysis = []
    for product_name, stores in sorted(product_table.items()):
        if len(stores) < 2:
            continue
        in_stock_prices = []
        for store, data in stores.items():
            if data.get('price') and data.get('in_stock', True):
                in_stock_prices.append((store, data['price']))
        if not in_stock_prices:
            continue

        min_store, min_price = min(in_stock_prices, key=lambda x: x[1])
        max_store, max_price = max(in_stock_prices, key=lambda x: x[1])
        avg = sum(p for _, p in in_stock_prices) / len(in_stock_prices)
        price_analysis.append({
            'name': product_name,
            'min': (min_store, min_price),
            'max': (max_store, max_price),
            'avg': avg,
            'count': len(in_stock_prices),
        })

    msgs = []
    current = ""
    for pa in price_analysis:
        line = (
            f"📦 <b>{esc(pa['name'])}</b>\n"
            f"  🟢 Мін: <b>₴{pa['min'][1]}</b> ({pa['min'][0]})\n"
            f"  🔴 Макс: <b>₴{pa['max'][1]}</b> ({pa['max'][0]})\n"
            f"  📊 Середня: <b>₴{int(pa['avg'])}</b> ({pa['count']} магаз.)\n"
        )
        if len(current) + len(line) > 3500:
            msgs.append(current)
            current = ""
        current += line + "\n"
    if current:
        msgs.append(current)
    for m in msgs:
        send_tg(m)
        time.sleep(1.5)

    # === PART 3: Average prices ===
    send_tg("\n" + "━" * 30 + "\n"
            "📊 <b>ЧАСТИНА 3: Середня ціна по ринку</b>\n"
            "━" * 30)
    time.sleep(1.5)

    avg_msg = ""
    for pa in sorted(price_analysis, key=lambda x: x['avg'], reverse=True):
        avg_msg += f"• {esc(pa['name'])}: <b>₴{int(pa['avg'])}</b>\n"
        if len(avg_msg) > 3500:
            send_tg(avg_msg)
            avg_msg = ""
            time.sleep(1.5)
    if avg_msg:
        send_tg(avg_msg)
        time.sleep(1.5)

    # === PART 4: Availability matrix ===
    send_tg("\n" + "━" * 30 + "\n"
            "🗺 <b>ЧАСТИНА 4: Наявність по магазинах</b>\n"
            "━" * 30)
    time.sleep(1.5)

    avail_msg = ""
    for product_name, stores in sorted(product_table.items()):
        if 'eonni.com.ua' not in stores:
            continue
        store_list = [s for s in stores.keys() if s != 'eonni.com.ua']
        if store_list:
            store_names = ", ".join(store_list)
            avail_msg += f"✅ <b>{esc(product_name)}</b>\n   📍 {store_names}\n\n"
        else:
            avail_msg += f"🔒 <b>{esc(product_name)}</b>\n   📍 <i>тільки у вас!</i>\n\n"

        if len(avail_msg) > 3500:
            send_tg(avail_msg)
            avail_msg = ""
            time.sleep(1.5)
    if avail_msg:
        send_tg(avail_msg)
        time.sleep(1.5)

    # === EXCLUSIVE products ===
    exclusive = [name for name, stores in product_table.items()
                 if 'eonni.com.ua' in stores and len(stores) == 1]
    if exclusive:
        ex_msg = ("🌟 <b>Ексклюзивні товари (є тільки у вас!):</b>\n\n" +
                  "\n".join(f"• {esc(n)}" for n in sorted(exclusive)))
        for i in range(0, len(ex_msg), 4000):
            send_tg(ex_msg[i:i+4000])
            time.sleep(1.5)

    send_tg("✅ <b>Аналіз завершено!</b>\n\n"
            f"📊 Всього проаналізовано: {len(product_table)} товарів\n"
            f"🏬 Магазинів: {len(competitors) + 1}\n"
            f"🌟 Ексклюзивних товарів: {len(exclusive)}")


if __name__ == '__main__':
    main()
