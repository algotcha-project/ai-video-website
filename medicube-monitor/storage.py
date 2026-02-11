"""
JSON-based storage for tracking known products and configuration.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Default storage directory (next to this script)
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class ProductStorage:
    """Persistent storage for tracking known Medicube products."""

    def __init__(self, data_dir: str = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.products_file = os.path.join(data_dir, "known_products.json")
        self.config_file = os.path.join(data_dir, "config.json")
        self.history_file = os.path.join(data_dir, "check_history.json")

        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

    # --- Products ---

    def load_known_products(self) -> Dict[str, dict]:
        """Load all previously known products. Returns dict of product_no -> product data."""
        if not os.path.exists(self.products_file):
            return {}
        try:
            with open(self.products_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading products file: {e}")
            return {}

    def save_known_products(self, products: Dict[str, dict]) -> None:
        """Save the current set of known products."""
        try:
            with open(self.products_file, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(products)} products to storage")
        except IOError as e:
            logger.error(f"Error saving products file: {e}")

    def get_known_product_ids(self) -> Set[str]:
        """Get set of all known product IDs."""
        return set(self.load_known_products().keys())

    def find_new_products(self, current_products: Dict[str, dict]) -> Dict[str, dict]:
        """
        Compare current products with stored ones.
        Returns dict of only the NEW products (not seen before).
        """
        known_ids = self.get_known_product_ids()
        new_products = {
            pid: pdata
            for pid, pdata in current_products.items()
            if pid not in known_ids
        }
        return new_products

    def update_products(self, current_products: Dict[str, dict]) -> Dict[str, dict]:
        """
        Update the stored products with current ones.
        Returns the new products that weren't known before.
        """
        known = self.load_known_products()
        new_products = {
            pid: pdata
            for pid, pdata in current_products.items()
            if pid not in known
        }

        # Merge: update existing + add new
        known.update(current_products)

        # Add first_seen timestamp to new products
        now = datetime.now().isoformat()
        for pid in new_products:
            known[pid]["first_seen"] = now

        self.save_known_products(known)

        return new_products

    def is_first_run(self) -> bool:
        """Check if this is the first time the monitor runs."""
        return not os.path.exists(self.products_file)

    # --- Config ---

    def load_config(self) -> dict:
        """Load configuration."""
        if not os.path.exists(self.config_file):
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def save_config(self, config: dict) -> None:
        """Save configuration."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Error saving config: {e}")

    def get_chat_ids(self) -> List[str]:
        """Get list of Telegram chat IDs to notify."""
        config = self.load_config()
        return config.get("chat_ids", [])

    def save_chat_ids(self, chat_ids: List[str]) -> None:
        """Save Telegram chat IDs."""
        config = self.load_config()
        config["chat_ids"] = list(set(chat_ids))  # deduplicate
        self.save_config(config)

    def add_chat_id(self, chat_id: str) -> None:
        """Add a new chat ID if not already present."""
        chat_ids = self.get_chat_ids()
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            self.save_chat_ids(chat_ids)
            logger.info(f"Added chat ID: {chat_id}")

    # --- History ---

    def log_check(self, total_products: int, new_count: int,
                  new_product_ids: Optional[List[str]] = None) -> None:
        """Log a monitoring check to history."""
        history = self._load_history()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "total_products": total_products,
            "new_count": new_count,
        }
        if new_product_ids:
            entry["new_product_ids"] = new_product_ids

        history.append(entry)

        # Keep last 100 entries
        if len(history) > 100:
            history = history[-100:]

        self._save_history(history)

    def get_last_check(self) -> Optional[dict]:
        """Get the most recent check entry."""
        history = self._load_history()
        return history[-1] if history else None

    def _load_history(self) -> list:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self, history: list) -> None:
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"Error saving history: {e}")
