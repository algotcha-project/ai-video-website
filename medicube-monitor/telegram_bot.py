"""
Telegram bot module for sending Medicube product notifications.
"""

import logging
import requests
from typing import List, Optional

logger = logging.getLogger(__name__)


class TelegramBot:
    """Simple Telegram bot for sending product notifications."""

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, token: str, chat_ids: Optional[List[str]] = None):
        self.token = token
        self.chat_ids = chat_ids or []
        self.api_url = self.API_BASE.format(token=token)

    def verify(self) -> bool:
        """Verify the bot token is valid."""
        try:
            resp = requests.get(f"{self.api_url}/getMe", timeout=10)
            data = resp.json()
            if data.get("ok"):
                bot_info = data["result"]
                logger.info(
                    f"Bot verified: @{bot_info['username']} ({bot_info['first_name']})"
                )
                return True
            else:
                logger.error(f"Bot verification failed: {data}")
                return False
        except Exception as e:
            logger.error(f"Bot verification error: {e}")
            return False

    def discover_chat_ids(self) -> List[str]:
        """
        Discover chat IDs from recent messages sent to the bot.
        Users need to send /start to the bot first.
        """
        try:
            resp = requests.get(f"{self.api_url}/getUpdates", timeout=10)
            data = resp.json()
            if not data.get("ok"):
                logger.warning(f"Failed to get updates: {data}")
                return []

            discovered = set()
            for update in data.get("result", []):
                msg = update.get("message", {})
                chat = msg.get("chat", {})
                chat_id = str(chat.get("id", ""))
                if chat_id:
                    discovered.add(chat_id)
                    chat_name = (
                        chat.get("title")
                        or chat.get("first_name", "")
                        + " "
                        + chat.get("last_name", "")
                    ).strip()
                    logger.info(f"Discovered chat: {chat_id} ({chat_name})")

            return list(discovered)
        except Exception as e:
            logger.error(f"Error discovering chat IDs: {e}")
            return []

    def send_message(self, chat_id: str, text: str,
                     parse_mode: str = "HTML",
                     disable_web_page_preview: bool = False) -> bool:
        """Send a text message to a specific chat."""
        try:
            resp = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": disable_web_page_preview,
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("ok"):
                return True
            else:
                logger.error(f"Failed to send message to {chat_id}: {data}")
                return False
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False

    def broadcast(self, text: str, **kwargs) -> int:
        """Send a message to all known chat IDs. Returns count of successful sends."""
        success = 0
        for chat_id in self.chat_ids:
            if self.send_message(chat_id, text, **kwargs):
                success += 1
        return success

    def send_new_product_alert(self, product: dict) -> int:
        """
        Send a formatted new product notification to all chats.
        product dict should have: name, url, price_uah, price_krw, product_no, category
        """
        name = product.get("name", "Unknown")
        url = product.get("url", "")
        price_uah = product.get("price_uah", "")
        price_krw = product.get("price_krw", "")
        product_no = product.get("product_no", "")
        category = product.get("category", "")

        lines = [
            "🆕 <b>Новий товар на Medicube!</b>",
            "",
            f"📦 <b>{_escape_html(name)}</b>",
        ]

        if price_uah:
            price_line = f"💰 Ціна: <b>{_escape_html(price_uah)}</b>"
            if price_krw:
                price_line += f" ({_escape_html(price_krw)})"
            lines.append(price_line)
        elif price_krw:
            lines.append(f"💰 Ціна: {_escape_html(price_krw)}")

        if category:
            lines.append(f"📂 Категорія: {_escape_html(category)}")

        lines.append(f"🔗 ID: #{product_no}")

        if url:
            lines.append(f"\n<a href=\"{url}\">👉 Перейти до товару</a>")

        text = "\n".join(lines)
        return self.broadcast(text)

    def send_summary(self, new_count: int, total_count: int) -> int:
        """Send a monitoring summary message."""
        if new_count > 0:
            text = (
                f"📊 <b>Моніторинг Medicube завершено</b>\n\n"
                f"🆕 Нових товарів: <b>{new_count}</b>\n"
                f"📦 Всього товарів на сайті: <b>{total_count}</b>\n\n"
                f"🌐 <a href=\"https://m.themedicube.co.kr/\">Перейти на сайт</a>"
            )
        else:
            text = (
                f"📊 <b>Моніторинг Medicube завершено</b>\n\n"
                f"✅ Нових товарів не знайдено\n"
                f"📦 Всього товарів на сайті: <b>{total_count}</b>"
            )
        return self.broadcast(text)

    def send_startup_message(self) -> int:
        """Send a startup/registration confirmation message."""
        text = (
            "🤖 <b>Medicube Monitor запущено!</b>\n\n"
            "Бот буде перевіряти нові товари на "
            "<a href=\"https://m.themedicube.co.kr/\">m.themedicube.co.kr</a> "
            "кожні 24 години та надсилати повідомлення про новинки.\n\n"
            "Команди:\n"
            "/start - Підписатися на оновлення\n"
            "/check - Перевірити зараз\n"
            "/status - Статус моніторингу"
        )
        return self.broadcast(text)


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
