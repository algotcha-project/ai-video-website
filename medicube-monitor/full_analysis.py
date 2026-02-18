#!/usr/bin/env python3
"""
Full competitive price analysis for ALL products on eonni.com.ua.
Scrapes eonni + all accessible competitors, matches products, sends report to TG.
Uses Playwright for JS-rendered / Cloudflare-protected sites.
"""

import re, json, time, logging, sys, os
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger()

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "uk-UA,uk;q=0.9",
}
TOKEN = "8450762615:AAF0j3A0bRhA0zejgLEZgma4t8nAvBtF2bg"
CHAT_ID = "300367602"
TG_API = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "data", "analysis_progress.json")


def send_tg(text):
    for _ in range(4):
        try:
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
                return False
        except:
            time.sleep(2)
    return False


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def extract_price(text):
    if not text:
        return None
    text = text.replace("\xa0", " ").replace("\u2009", " ")
    m = re.search(r"(\d[\d\s,]*)\s*(?:₴|грн)", text)
    if m:
        v = int(re.sub(r"[\s,]", "", m.group(1)))
        return v if v > 30 else None
    return None


def normalize(name):
    n = name.lower().strip()
    n = re.sub(r"\s+", " ", n)
    n = re.sub(r"\d+\s*(?:мл|ml|г|g)\b", "", n)
    n = re.sub(r"medicube\s*", "", n)
    n = re.sub(r"mediheal\s*", "", n)
    n = re.sub(r"vt\s*cosmetics?\s*", "", n)
    n = re.sub(r"[^\w\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


# =================== SCRAPERS ===================

def scrape_eonni():
    log.info("Scraping eonni.com.ua...")
    r = requests.get("https://eonni.com.ua/api/products", headers=H, timeout=15)
    data = r.json()
    products = []
    seen = set()
    for p in data:
        name = p.get("name", "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        price_raw = p.get("sale_price") or p.get("original_price")
        price = int(float(price_raw)) if price_raw and float(price_raw) > 50 else None
        stock = (p.get("stock_quantity") or 0) > 0
        products.append({
            "name": name,
            "price": price,
            "in_stock": stock,
            "url": f"https://eonni.com.ua/product/{p.get('id', '')}",
        })
    log.info(f"  eonni: {len(products)} products")
    return products


def scrape_lullaby():
    log.info("Scraping lullaby.ua...")
    r = requests.get("https://lullaby.ua/brands/medicube", headers=H, timeout=15)
    s = BeautifulSoup(r.text, "html.parser")
    build_id = None
    for sc in s.select("script[src*='_buildManifest']"):
        m = re.search(r"/([^/]+)/_buildManifest", sc.get("src", ""))
        if m:
            build_id = m.group(1)
            break
    if not build_id:
        return []

    all_products = []
    page = 1
    while True:
        url = f"https://lullaby.ua/_next/data/{build_id}/brands/medicube.json"
        if page > 1:
            url += f"?page={page}"
        r = requests.get(url, headers=H, timeout=15)
        if r.status_code != 200:
            break
        d = r.json()
        prods = d["pageProps"]["initialState"]["categories"]["category"]["products"]
        items = prods.get("data", [])
        if not items:
            break
        for p in items:
            pr = str(p.get("price", ""))
            price = int(float(pr)) if pr and float(pr) > 30 else None
            all_products.append({
                "name": p.get("title", ""),
                "name_en": p.get("title_en", ""),
                "price": price,
                "in_stock": (p.get("quantity") or 0) > 0,
                "url": f"https://lullaby.ua{p.get('url', '')}",
            })
        if len(all_products) >= prods.get("meta", {}).get("total", 0):
            break
        page += 1
        time.sleep(0.5)
    log.info(f"  lullaby: {len(all_products)}")
    return all_products


def scrape_hitomi():
    log.info("Scraping hitomi.com.ua...")
    products = []
    r = requests.get("https://hitomi.com.ua/ru/brend/medicube-ru/", headers=H, timeout=15)
    s = BeautifulSoup(r.text, "html.parser")
    container = s.select_one(".products")
    if not container:
        return products
    for wp in container.find_all("div", recursive=False):
        classes = " ".join(wp.get("class", []))
        if "product" not in classes:
            continue
        link_el = wp.select_one("a[href*='/product/']")
        if not link_el:
            continue
        name = ""
        img = wp.select_one("img")
        if img:
            name = img.get("alt", "").strip()
        if not name:
            continue
        price = None
        ins_bdi = wp.select_one(".price ins bdi")
        if ins_bdi:
            m = re.match(r"([\d,]+)", ins_bdi.get_text(strip=True))
            if m:
                price = int(m.group(1).replace(",", ""))
        if not price:
            bdi = wp.select_one(".price bdi")
            if bdi and not bdi.find_parent("del"):
                m = re.match(r"([\d,]+)", bdi.get_text(strip=True))
                if m:
                    price = int(m.group(1).replace(",", ""))
        in_stock = "instock" in classes
        if price and price > 30:
            products.append({
                "name": name, "price": price, "in_stock": in_stock,
                "url": link_el.get("href", ""),
            })
    log.info(f"  hitomi: {len(products)}")
    return products


def _scrape_with_playwright(stores_config):
    """Scrape multiple stores using a single Playwright browser session."""
    from playwright.sync_api import sync_playwright
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="uk-UA",
        )

        for store_name, config in stores_config.items():
            log.info(f"Scraping {store_name} (Playwright)...")
            products = []
            try:
                page = ctx.new_page()
                page.goto(config["url"], timeout=45000, wait_until="networkidle")
                time.sleep(config.get("wait", 4))

                # Scroll to load lazy content
                total_h = page.evaluate("document.body.scrollHeight")
                for i in range(0, min(total_h, 15000), 500):
                    page.evaluate(f"window.scrollTo(0, {i})")
                    time.sleep(0.2)
                time.sleep(2)

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Use store-specific extraction
                extractor = config.get("extractor")
                if extractor:
                    products = extractor(soup, page)

                page.close()
            except Exception as e:
                log.error(f"  {store_name} error: {e}")
                try:
                    page.close()
                except:
                    pass

            results[store_name] = products
            log.info(f"  {store_name}: {len(products)}")
            time.sleep(1)

        browser.close()
    return results


def _extract_krkr(soup, page):
    """Extract products from krkr.com.ua using JS tree walker."""
    result = page.evaluate("""
        () => {
            const items = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            const priceNodes = [];
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent;
                if (t.includes('грн') && /\\d/.test(t)) priceNodes.push(walker.currentNode.parentElement);
            }
            for (const pn of priceNodes) {
                let card = pn;
                for (let i = 0; i < 6; i++) {
                    if (!card.parentElement) break;
                    card = card.parentElement;
                    const link = card.querySelector('a[href]');
                    const img = card.querySelector('img[alt]');
                    if (link && img && img.alt.length > 10) {
                        items.push({
                            name: img.alt.substring(0, 120),
                            price: pn.textContent.trim().substring(0, 30),
                            href: link.href,
                        });
                        break;
                    }
                }
            }
            const seen = new Set();
            return items.filter(i => { if(seen.has(i.name)) return false; seen.add(i.name); return true; });
        }
    """)
    products = []
    for r in result:
        price = extract_price(r["price"])
        if price:
            products.append({
                "name": r["name"], "price": price, "in_stock": True, "url": r["href"],
            })
    return products


def _extract_shine_bright(soup, page):
    """Extract products from shine-bright.com.ua OpenCart AJAX."""
    products = []
    for el in soup.find_all(string=re.compile(r"\d.*грн")):
        text = el.strip()
        m = re.search(r"(\d[\d\s]*)\s*грн", text)
        if not m:
            continue
        price = int(re.sub(r"\s", "", m.group(1)))
        if price < 50:
            continue
        parent = el.parent
        for _ in range(10):
            if not parent:
                break
            link = parent.select_one("a[href]")
            if link:
                name = link.get_text(strip=True)
                if len(name) > 10:
                    products.append({
                        "name": name[:120], "price": price,
                        "in_stock": True, "url": link.get("href", ""),
                    })
                    break
            parent = parent.parent
    seen = set()
    return [p for p in products if p["name"] not in seen and not seen.add(p["name"])]


# =================== MATCHING ===================

def match_products(eonni_products, competitor_products, store_name):
    """Match competitor products to eonni products. Returns list of (eonni_name, comp_data)."""
    matches = []
    for cp in competitor_products:
        best_score = 0
        best_match = None
        cn = cp["name"]
        for ep in eonni_products:
            en = ep["name"]
            score = similarity(cn, en)
            if score > best_score:
                best_score = score
                best_match = en
            # Also try matching name_en if available
            name_en = cp.get("name_en", "")
            if name_en:
                score2 = similarity(name_en, en)
                if score2 > best_score:
                    best_score = score2
                    best_match = en

        if best_score >= 0.45:
            matches.append((best_match, cp))

    return matches


# =================== MAIN ===================

def main():
    log.info("=" * 60)
    log.info("FULL COMPETITIVE ANALYSIS — ALL PRODUCTS")
    log.info("=" * 60)

    # 1. Scrape eonni
    eonni = scrape_eonni()

    # 2. Scrape competitors (HTTP-based)
    competitors = {}
    for name, func in [("lullaby.ua", scrape_lullaby), ("hitomi.com.ua", scrape_hitomi)]:
        try:
            competitors[name] = func()
        except Exception as e:
            log.error(f"  {name}: {e}")
            competitors[name] = []
        time.sleep(1)

    # 3. Scrape Playwright-based stores
    pw_stores = {
        "krkr.com.ua": {
            "url": "https://krkr.com.ua/medicube/",
            "wait": 5,
            "extractor": _extract_krkr,
        },
        "shine-bright.com.ua": {
            "url": "https://shine-bright.com.ua/ua/medicube?limit=100&ajax=1",
            "wait": 3,
            "extractor": _extract_shine_bright,
        },
    }
    pw_results = _scrape_with_playwright(pw_stores)
    competitors.update(pw_results)

    # 4. Build product table
    product_table = defaultdict(dict)  # eonni_name -> {store: {price, in_stock, url, comp_name}}

    for p in eonni:
        product_table[p["name"]]["eonni.com.ua"] = {
            "price": p["price"], "in_stock": p["in_stock"], "url": p["url"],
        }

    for store_name, store_products in competitors.items():
        matches = match_products(eonni, store_products, store_name)
        for eonni_name, cp in matches:
            product_table[eonni_name][store_name] = {
                "price": cp["price"],
                "in_stock": cp.get("in_stock", True),
                "url": cp.get("url", ""),
                "comp_name": cp["name"],
            }

    log.info(f"\nTotal eonni products: {len(eonni)}")
    log.info(f"Matched in competitors: {sum(1 for v in product_table.values() if len(v) > 1)}")

    # 5. Send report to Telegram
    send_report(eonni, competitors, product_table)


def send_report(eonni, competitors, product_table):
    store_names = ["eonni.com.ua"] + list(competitors.keys())

    # Header
    comp_summary = "\n".join(f"  🏬 {s}: {len(competitors[s])} товарів" for s in competitors)
    send_tg(
        f"📊 <b>ПОВНИЙ КОНКУРЕНТНИЙ АНАЛІЗ</b>\n\n"
        f"🏠 eonni.com.ua: <b>{len(eonni)}</b> товарів\n"
        f"{comp_summary}\n\n"
        f"🔗 Товарів з конкурентами: <b>{sum(1 for v in product_table.values() if len(v) > 1)}</b>"
    )
    time.sleep(2)

    # PART 1: Prices per product per store
    send_tg("━" * 30 + "\n📋 <b>ЧАСТИНА 1: Ціни по магазинах</b>\n" + "━" * 30)
    time.sleep(1.5)

    batch = ""
    for pname in sorted(product_table.keys()):
        stores = product_table[pname]
        if len(stores) < 2:
            continue
        lines = [f"📦 <b>{esc(pname)}</b>"]
        for s in store_names:
            if s not in stores:
                continue
            d = stores[s]
            p = d.get("price")
            stock = "✅" if d.get("in_stock", True) else "❌"
            icon = "🏠" if s == "eonni.com.ua" else "🏬"
            price_str = f"<b>₴{p}</b>" if p else "—"
            cn = d.get("comp_name", "")
            name_note = f" <i>({esc(cn[:35])})</i>" if cn and cn != pname else ""
            lines.append(f"  {icon} {s}: {price_str} {stock}{name_note}")
        entry = "\n".join(lines) + "\n\n"
        if len(batch) + len(entry) > 3800:
            send_tg(batch)
            batch = ""
            time.sleep(1.5)
        batch += entry
    if batch:
        send_tg(batch)
        time.sleep(1.5)

    # PART 2: Min/Max/Avg
    send_tg("━" * 30 + "\n📈 <b>ЧАСТИНА 2: Мін / Макс / Середня ціна</b>\n(тільки в наявності)\n" + "━" * 30)
    time.sleep(1.5)

    analysis = []
    for pname, stores in sorted(product_table.items()):
        if len(stores) < 2:
            continue
        prices = [(s, d["price"]) for s, d in stores.items() if d.get("price") and d.get("in_stock", True)]
        if not prices:
            continue
        mn_s, mn_p = min(prices, key=lambda x: x[1])
        mx_s, mx_p = max(prices, key=lambda x: x[1])
        avg = sum(p for _, p in prices) / len(prices)
        analysis.append({"name": pname, "min": (mn_s, mn_p), "max": (mx_s, mx_p), "avg": avg, "n": len(prices)})

    batch = ""
    for a in analysis:
        entry = (
            f"📦 <b>{esc(a['name'])}</b>\n"
            f"  🟢 Мін: <b>₴{a['min'][1]}</b> ({a['min'][0]})\n"
            f"  🔴 Макс: <b>₴{a['max'][1]}</b> ({a['max'][0]})\n"
            f"  📊 Сер: <b>₴{int(a['avg'])}</b> ({a['n']} магаз.)\n\n"
        )
        if len(batch) + len(entry) > 3800:
            send_tg(batch)
            batch = ""
            time.sleep(1.5)
        batch += entry
    if batch:
        send_tg(batch)
        time.sleep(1.5)

    # PART 3: Average prices (sorted)
    send_tg("━" * 30 + "\n📊 <b>ЧАСТИНА 3: Середня ціна (від дорогих до дешевих)</b>\n" + "━" * 30)
    time.sleep(1.5)
    batch = ""
    for a in sorted(analysis, key=lambda x: -x["avg"]):
        entry = f"• {esc(a['name'])}: <b>₴{int(a['avg'])}</b>\n"
        if len(batch) + len(entry) > 3800:
            send_tg(batch)
            batch = ""
            time.sleep(1.5)
        batch += entry
    if batch:
        send_tg(batch)
        time.sleep(1.5)

    # PART 4: Availability
    send_tg("━" * 30 + "\n🗺 <b>ЧАСТИНА 4: Наявність по магазинах</b>\n" + "━" * 30)
    time.sleep(1.5)

    exclusive = []
    batch = ""
    for pname in sorted(product_table.keys()):
        stores = product_table[pname]
        if "eonni.com.ua" not in stores:
            continue
        others = [s for s in stores if s != "eonni.com.ua"]
        if others:
            entry = f"✅ <b>{esc(pname)}</b>\n   📍 {', '.join(others)}\n\n"
        else:
            exclusive.append(pname)
            entry = f"🔒 <b>{esc(pname)}</b> — <i>тільки у вас</i>\n\n"
        if len(batch) + len(entry) > 3800:
            send_tg(batch)
            batch = ""
            time.sleep(1.5)
        batch += entry
    if batch:
        send_tg(batch)
        time.sleep(1.5)

    # Exclusive summary
    if exclusive:
        ex_text = "🌟 <b>Ексклюзив — тільки у вас:</b>\n\n" + "\n".join(f"• {esc(n)}" for n in exclusive)
        for i in range(0, len(ex_text), 3800):
            send_tg(ex_text[i:i+3800])
            time.sleep(1.5)

    # Not accessible stores
    blocked = ["lovelybunny.com.ua", "ksisters.com.ua", "eva.ua"]
    no_medicube = ["sisters.co.ua", "koreanstory.com.ua", "kylkalyaba.com.ua", "beautysmart.com.ua", "isei.ua"]
    send_tg(
        "━" * 30 + "\n"
        "⚠️ <b>Магазини що не вдалося проаналізувати:</b>\n\n"
        "<b>Cloudflare блокує:</b>\n" +
        "\n".join(f"  🚫 {s}" for s in blocked) + "\n\n"
        "<b>Не знайдено товарів / пошук не працює:</b>\n" +
        "\n".join(f"  ❓ {s}" for s in no_medicube)
    )
    time.sleep(1)

    # Final summary
    send_tg(
        "✅ <b>Аналіз завершено!</b>\n\n"
        f"📦 Ваших товарів: <b>{len(eonni)}</b>\n"
        f"🏬 Конкурентів з даними: <b>{len(competitors)}</b>\n"
        f"🔗 Товарів у конкурентів: <b>{sum(1 for v in product_table.values() if len(v) > 1)}</b>\n"
        f"🌟 Ексклюзив: <b>{len(exclusive)}</b>\n"
        f"📈 З цінами для порівняння: <b>{len(analysis)}</b>"
    )


if __name__ == "__main__":
    main()
