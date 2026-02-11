"""
Currency conversion module.
Fetches live KRW → UAH exchange rate and converts prices.
"""

import re
import logging
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Fallback rate in case all APIs fail (will be stale but better than nothing)
_FALLBACK_RATE: Optional[float] = None


def get_krw_to_uah_rate() -> float:
    """
    Fetch the current KRW → UAH exchange rate from public APIs.
    Tries multiple sources for reliability.
    Returns rate as float (e.g. 0.0295 means 1 KRW = 0.0295 UAH).
    """
    global _FALLBACK_RATE

    # Source 1: exchangerate-api.com (free, no key needed)
    try:
        resp = requests.get(
            "https://api.exchangerate-api.com/v4/latest/KRW",
            timeout=10,
        )
        resp.raise_for_status()
        rate = resp.json()["rates"]["UAH"]
        logger.info(f"Exchange rate (exchangerate-api): 1 KRW = {rate} UAH")
        _FALLBACK_RATE = rate
        return rate
    except Exception as e:
        logger.warning(f"exchangerate-api.com failed: {e}")

    # Source 2: open.er-api.com (free, no key needed)
    try:
        resp = requests.get(
            "https://open.er-api.com/v6/latest/KRW",
            timeout=10,
        )
        resp.raise_for_status()
        rate = resp.json()["rates"]["UAH"]
        logger.info(f"Exchange rate (open.er-api): 1 KRW = {rate} UAH")
        _FALLBACK_RATE = rate
        return rate
    except Exception as e:
        logger.warning(f"open.er-api.com failed: {e}")

    # Source 3: via USD as intermediate (frankfurter.app - ECB data)
    try:
        resp = requests.get(
            "https://api.frankfurter.app/latest?from=KRW&to=UAH",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"].get("UAH")
        if rate:
            logger.info(f"Exchange rate (frankfurter): 1 KRW = {rate} UAH")
            _FALLBACK_RATE = rate
            return rate
    except Exception as e:
        logger.warning(f"frankfurter.app failed: {e}")

    # Fallback: use last known rate or a hardcoded approximate
    if _FALLBACK_RATE:
        logger.warning(f"Using cached fallback rate: 1 KRW = {_FALLBACK_RATE} UAH")
        return _FALLBACK_RATE

    # Last resort: approximate rate (updated Feb 2026)
    fallback = 0.03
    logger.warning(f"All APIs failed! Using hardcoded fallback: 1 KRW = {fallback} UAH")
    return fallback


def parse_krw_price(price_str: str) -> Optional[int]:
    """
    Parse a Korean Won price string like '329,000원' into integer (329000).
    Returns None if parsing fails.
    """
    if not price_str:
        return None
    # Remove everything except digits and commas, then strip commas
    cleaned = re.sub(r"[^\d,]", "", price_str)
    cleaned = cleaned.replace(",", "")
    if cleaned:
        try:
            return int(cleaned)
        except ValueError:
            return None
    return None


def krw_to_uah(price_krw: int, rate: float) -> float:
    """Convert KRW amount to UAH using the given rate."""
    return round(price_krw * rate, 2)


def format_uah(amount: float) -> str:
    """Format UAH amount nicely: '1 234.50 грн'."""
    if amount >= 1000:
        # Format with space as thousands separator
        integer_part = int(amount)
        decimal_part = round(amount - integer_part, 2)
        formatted_int = f"{integer_part:,}".replace(",", " ")
        if decimal_part > 0:
            return f"{formatted_int}.{int(decimal_part * 100):02d} грн"
        return f"{formatted_int} грн"
    else:
        if amount == int(amount):
            return f"{int(amount)} грн"
        return f"{amount:.2f} грн"


def convert_price(price_str: str, rate: Optional[float] = None) -> Tuple[str, str]:
    """
    Convert a KRW price string to UAH.
    Returns tuple of (uah_formatted, krw_original).
    If conversion fails, returns ("", original_price).
    """
    if not price_str:
        return ("", "")

    krw_amount = parse_krw_price(price_str)
    if krw_amount is None:
        return ("", price_str)

    if rate is None:
        rate = get_krw_to_uah_rate()

    uah_amount = krw_to_uah(krw_amount, rate)
    return (format_uah(uah_amount), price_str)
