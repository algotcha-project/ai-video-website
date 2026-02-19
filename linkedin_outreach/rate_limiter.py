"""
Rate limiter and schedule enforcer.
Tracks daily action counts, enforces working hours, and implements
the warmup period for new accounts.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .config import RateLimits

logger = logging.getLogger(__name__)

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class RateLimiter:
    def __init__(self, rate_limits: RateLimits, data_dir: str, campaign_name: str):
        self._limits = rate_limits
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._counter_path = self._dir / f"{campaign_name}_daily_counters.json"
        self._start_path = self._dir / f"{campaign_name}_start_date.txt"
        self._counters: dict = {}
        self._campaign_start: datetime = self._load_start_date()
        self._load_counters()

    def _load_start_date(self) -> datetime:
        if self._start_path.exists():
            raw = self._start_path.read_text().strip()
            return datetime.fromisoformat(raw)
        now = datetime.utcnow()
        self._start_path.write_text(now.isoformat())
        return now

    def _load_counters(self) -> None:
        today = self._today_key()
        if self._counter_path.exists():
            with open(self._counter_path, "r") as f:
                self._counters = json.load(f)
        if today not in self._counters:
            self._counters[today] = {
                "connection_requests": 0,
                "messages": 0,
                "profile_views": 0,
            }
            self._save_counters()

    def _save_counters(self) -> None:
        with open(self._counter_path, "w") as f:
            json.dump(self._counters, f, indent=2)

    @staticmethod
    def _today_key() -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _warmup_multiplier(self) -> float:
        if not self._limits.warmup_enabled:
            return 1.0
        days_active = (datetime.utcnow() - self._campaign_start).days
        if days_active >= self._limits.warmup_days:
            return 1.0
        progress = days_active / self._limits.warmup_days
        return self._limits.warmup_start_pct + (1.0 - self._limits.warmup_start_pct) * progress

    def effective_limit(self, base_limit: int) -> int:
        return max(1, int(base_limit * self._warmup_multiplier()))

    def is_within_working_hours(self) -> bool:
        now = datetime.now()
        day = DAY_ABBR[now.weekday()]
        if day not in self._limits.active_days:
            return False
        hour = now.hour
        return self._limits.daily_start_hour <= hour < self._limits.daily_end_hour

    def can_send_connection_request(self) -> bool:
        today = self._today_key()
        if today not in self._counters:
            self._counters[today] = {"connection_requests": 0, "messages": 0, "profile_views": 0}
        current = self._counters[today]["connection_requests"]
        limit = self.effective_limit(self._limits.max_connection_requests_per_day)
        return current < limit

    def can_send_message(self) -> bool:
        today = self._today_key()
        if today not in self._counters:
            self._counters[today] = {"connection_requests": 0, "messages": 0, "profile_views": 0}
        current = self._counters[today]["messages"]
        limit = self.effective_limit(self._limits.max_messages_per_day)
        return current < limit

    def can_view_profile(self) -> bool:
        today = self._today_key()
        if today not in self._counters:
            self._counters[today] = {"connection_requests": 0, "messages": 0, "profile_views": 0}
        current = self._counters[today]["profile_views"]
        limit = self.effective_limit(self._limits.max_profile_views_per_day)
        return current < limit

    def record_connection_request(self) -> None:
        today = self._today_key()
        self._counters.setdefault(today, {"connection_requests": 0, "messages": 0, "profile_views": 0})
        self._counters[today]["connection_requests"] += 1
        self._save_counters()

    def record_message(self) -> None:
        today = self._today_key()
        self._counters.setdefault(today, {"connection_requests": 0, "messages": 0, "profile_views": 0})
        self._counters[today]["messages"] += 1
        self._save_counters()

    def record_profile_view(self) -> None:
        today = self._today_key()
        self._counters.setdefault(today, {"connection_requests": 0, "messages": 0, "profile_views": 0})
        self._counters[today]["profile_views"] += 1
        self._save_counters()

    def wait_until_working_hours(self) -> None:
        while not self.is_within_working_hours():
            logger.info("Outside working hours. Sleeping 5 minutes...")
            time.sleep(300)

    def today_stats(self) -> dict:
        today = self._today_key()
        counters = self._counters.get(today, {})
        mult = self._warmup_multiplier()
        return {
            "date": today,
            "warmup_multiplier": f"{mult:.0%}",
            "connection_requests": f"{counters.get('connection_requests', 0)} / {self.effective_limit(self._limits.max_connection_requests_per_day)}",
            "messages": f"{counters.get('messages', 0)} / {self.effective_limit(self._limits.max_messages_per_day)}",
            "profile_views": f"{counters.get('profile_views', 0)} / {self.effective_limit(self._limits.max_profile_views_per_day)}",
        }
