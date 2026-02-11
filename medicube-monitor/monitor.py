#!/usr/bin/env python3
"""
Medicube Product Monitor
========================
Main monitoring script that:
1. Scrapes all products from m.themedicube.co.kr
2. Compares with previously known products
3. Sends Telegram notifications for new products
4. Runs on a schedule (default: every 24 hours)

Usage:
    python monitor.py                  # Run once and exit
    python monitor.py --daemon         # Run continuously every 24h
    python monitor.py --check          # Force check now
    python monitor.py --setup          # Initial setup (discover chat IDs)
    python monitor.py --interval 12    # Check every 12 hours (daemon mode)
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime

from scraper import scrape_all_products
from storage import ProductStorage
from telegram_bot import TelegramBot

# --- Configuration ---
BOT_TOKEN = os.environ.get(
    "MEDICUBE_BOT_TOKEN",
    "8450762615:AAF0j3A0bRhA0zejgLEZgma4t8nAvBtF2bg",
)
DEFAULT_INTERVAL_HOURS = 24
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --- Logging setup ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(DATA_DIR, "monitor.log"),
                encoding="utf-8",
            ),
        ],
    )


logger = logging.getLogger("medicube-monitor")


def run_check(storage: ProductStorage, bot: TelegramBot, silent_first_run: bool = True) -> int:
    """
    Run a single product check cycle.
    Returns the number of new products found.
    """
    logger.info("=" * 60)
    logger.info("Starting product check...")
    logger.info(f"Time: {datetime.now().isoformat()}")

    is_first = storage.is_first_run()

    # Step 1: Scrape current products
    logger.info("Scraping Medicube website...")
    try:
        current_products_raw = scrape_all_products()
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        bot.broadcast("⚠️ <b>Помилка моніторингу</b>\n\nНе вдалося перевірити сайт Medicube. Перевірте логи.")
        return 0

    if not current_products_raw:
        logger.warning("No products found! The website might be down or changed.")
        bot.broadcast("⚠️ <b>Увага!</b>\n\nНе знайдено жодного товару на сайті Medicube. Можливо, сайт недоступний або змінив структуру.")
        return 0

    # Convert to dicts for storage
    current_products = {
        pid: p.to_dict() for pid, p in current_products_raw.items()
    }

    total_count = len(current_products)
    logger.info(f"Found {total_count} products on the website")

    # Step 2: Compare with known products
    if is_first:
        logger.info("First run - saving all products as baseline (no notifications)")
        storage.update_products(current_products)
        storage.log_check(total_count, 0)

        if not silent_first_run:
            bot.send_summary(0, total_count)
        
        logger.info(f"Baseline saved: {total_count} products")
        return 0

    new_products = storage.find_new_products(current_products)
    new_count = len(new_products)

    logger.info(f"New products found: {new_count}")

    # Step 3: Send notifications for each new product
    if new_count > 0:
        logger.info(f"Sending notifications for {new_count} new products...")
        for pid, pdata in sorted(new_products.items(), key=lambda x: int(x[0])):
            logger.info(f"  NEW: #{pid} - {pdata.get('name', 'Unknown')}")
            bot.send_new_product_alert(pdata)
            time.sleep(0.5)  # Rate limit

        # Send summary
        bot.send_summary(new_count, total_count)

    # Step 4: Update storage
    storage.update_products(current_products)
    storage.log_check(total_count, new_count, list(new_products.keys()) if new_products else None)

    logger.info(f"Check complete. {new_count} new products, {total_count} total.")
    logger.info("=" * 60)

    return new_count


def setup_mode(storage: ProductStorage, bot: TelegramBot):
    """Interactive setup: discover chat IDs and send test message."""
    print("\n" + "=" * 50)
    print("  Medicube Monitor - Setup")
    print("=" * 50)

    # Verify bot
    print("\n1. Verifying bot token...")
    if not bot.verify():
        print("   ERROR: Bot token is invalid!")
        sys.exit(1)
    print("   OK - Bot is valid")

    # Discover chat IDs
    print("\n2. Discovering chat IDs...")
    print("   Make sure you have sent /start to the bot first!")
    print("   Bot: @KoreanEonni_bot")

    discovered = bot.discover_chat_ids()
    existing = storage.get_chat_ids()

    all_ids = list(set(existing + discovered))

    if not all_ids:
        print("\n   No chat IDs found!")
        print("   Please send /start to the bot and run setup again.")
        manual = input("   Or enter a chat ID manually (leave empty to skip): ").strip()
        if manual:
            all_ids = [manual]
        else:
            print("   Setup incomplete - no chat IDs configured.")
            return

    storage.save_chat_ids(all_ids)
    bot.chat_ids = all_ids
    print(f"   Found {len(all_ids)} chat(s): {', '.join(all_ids)}")

    # Send test message
    print("\n3. Sending test message...")
    sent = bot.send_startup_message()
    print(f"   Sent to {sent}/{len(all_ids)} chats")

    # Run initial scrape
    print("\n4. Running initial product scan...")
    run_check(storage, bot, silent_first_run=False)

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("  Run with --daemon to start continuous monitoring")
    print("=" * 50 + "\n")


def daemon_mode(storage: ProductStorage, bot: TelegramBot, interval_hours: float):
    """Run the monitor continuously on a schedule."""
    interval_seconds = interval_hours * 3600

    logger.info(f"Starting daemon mode (check every {interval_hours}h)")

    # Handle graceful shutdown
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Shutdown signal received. Exiting...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initial check
    run_check(storage, bot)

    while running:
        next_check = datetime.now().timestamp() + interval_seconds
        next_check_time = datetime.fromtimestamp(next_check).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Next check at: {next_check_time}")

        # Sleep in small intervals to allow graceful shutdown
        while running and time.time() < next_check:
            time.sleep(60)  # Check every minute if we should stop

        if running:
            try:
                run_check(storage, bot)
            except Exception as e:
                logger.error(f"Check failed: {e}", exc_info=True)
                try:
                    bot.broadcast(
                        f"⚠️ <b>Помилка моніторингу</b>\n\n"
                        f"Сталася помилка: {str(e)[:200]}"
                    )
                except Exception:
                    pass

    logger.info("Monitor stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Medicube Korea Product Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run continuously on a schedule",
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Run a single check and exit",
    )
    parser.add_argument(
        "--setup", "-s",
        action="store_true",
        help="Run interactive setup",
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=DEFAULT_INTERVAL_HOURS,
        help=f"Check interval in hours (default: {DEFAULT_INTERVAL_HOURS})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--token", "-t",
        default=BOT_TOKEN,
        help="Telegram bot token (or set MEDICUBE_BOT_TOKEN env var)",
    )
    parser.add_argument(
        "--chat-id",
        action="append",
        dest="chat_ids",
        help="Telegram chat ID(s) to notify (can be used multiple times)",
    )

    args = parser.parse_args()

    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Setup logging
    setup_logging(args.verbose)

    # Initialize storage
    storage = ProductStorage(DATA_DIR)

    # Initialize bot
    chat_ids = args.chat_ids or storage.get_chat_ids()

    # Auto-discover chat IDs if none configured
    bot = TelegramBot(args.token, chat_ids)

    if not chat_ids:
        logger.info("No chat IDs configured, trying to discover...")
        discovered = bot.discover_chat_ids()
        if discovered:
            storage.save_chat_ids(discovered)
            bot.chat_ids = discovered
            logger.info(f"Discovered {len(discovered)} chat(s)")
        else:
            logger.warning(
                "No chat IDs found! Send /start to @KoreanEonni_bot first, "
                "then run with --setup"
            )
            if not args.setup:
                logger.warning("Continuing without notifications (scrape-only mode)")

    # Run
    if args.setup:
        setup_mode(storage, bot)
    elif args.daemon:
        daemon_mode(storage, bot, args.interval)
    elif args.check:
        run_check(storage, bot, silent_first_run=False)
    else:
        # Default: single check
        run_check(storage, bot)


if __name__ == "__main__":
    main()
