"""
Multi-account manager.

Coordinates multiple LinkedIn accounts running in parallel with:
- Staggered scheduling (accounts operate in different time windows)
- Audience segmentation (each account targets a different slice)
- Shared de-duplication (no prospect is contacted by two accounts)
- Per-account rate limiting and warmup
- Sequential execution to keep resource usage sane
"""

import logging
import time
import random
from copy import deepcopy
from datetime import datetime
from typing import Optional
from pathlib import Path

from .config import CampaignConfig, AccountConfig, SearchCriteria, RateLimits, LinkedInCredentials
from .linkedin_client import LinkedInClient
from .prospect_store import ProspectStore, Prospect
from .prospect_finder import ProspectFinder
from .message_engine import MessageEngine
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AccountWorker:
    """Manages a single account's outreach within the multi-account system."""

    def __init__(
        self,
        account: AccountConfig,
        config: CampaignConfig,
        global_store: ProspectStore,
    ):
        self.account = account
        self.config = config
        self.name = account.name

        rate_limits = deepcopy(config.rate_limits)
        rate_limits.daily_start_hour = account.start_hour
        rate_limits.daily_end_hour = account.end_hour

        self.client = LinkedInClient(
            credentials=account.credentials,
            rate_limits=rate_limits,
            proxy=account.proxy,
            account_name=account.name,
        )

        self.store = global_store

        search = self._build_search_criteria(account, config.search)
        self.finder = ProspectFinder(self.client, self.store, search)

        self.limiter = RateLimiter(
            rate_limits,
            config.data_dir,
            f"{config.campaign_name}_{account.name}",
        )

        self.messages = MessageEngine(config.messages)
        self._connected = False

    @staticmethod
    def _build_search_criteria(account: AccountConfig, base: SearchCriteria) -> SearchCriteria:
        """
        Build account-specific search criteria by overlaying the account's
        segment overrides onto the global search criteria.
        """
        search = deepcopy(base)
        if account.job_titles:
            search.job_titles = account.job_titles
        if account.industries:
            search.industries = account.industries
        if account.locations:
            search.locations = account.locations
        return search

    def connect(self) -> bool:
        try:
            self.client.connect()
            own = self.client.get_own_profile()
            your_name = f"{own.get('firstName', '')} {own.get('lastName', '')}".strip()
            self.messages._your_name = your_name
            logger.info(f"[{self.name}] Logged in as: {your_name}")
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"[{self.name}] Failed to connect: {e}")
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def is_in_time_window(self) -> bool:
        now = datetime.now()
        day = DAY_ABBR[now.weekday()]
        if day not in self.config.rate_limits.active_days:
            return False
        return self.account.start_hour <= now.hour < self.account.end_hour

    def run_cycle(self) -> dict:
        summary = {
            "account": self.name,
            "prospects_found": 0,
            "connection_requests_sent": 0,
            "connections_accepted": 0,
            "followups_sent": 0,
            "errors": 0,
            "skipped": False,
        }

        if not self._connected:
            logger.warning(f"[{self.name}] Not connected, skipping cycle.")
            summary["skipped"] = True
            return summary

        if not self.is_in_time_window():
            logger.info(
                f"[{self.name}] Outside time window "
                f"({self.account.start_hour}:00-{self.account.end_hour}:00), skipping."
            )
            summary["skipped"] = True
            return summary

        logger.info(f"[{self.name}] --- Searching for prospects ---")
        try:
            new_prospects = self.finder.search_and_store(limit=30)
            summary["prospects_found"] = len(new_prospects)
            for p in new_prospects:
                p.tags.append(f"account:{self.name}")
                self.store.save()
        except Exception as e:
            logger.error(f"[{self.name}] Search failed: {e}")
            summary["errors"] += 1

        logger.info(f"[{self.name}] --- Sending connection requests ---")
        for prospect in self._get_my_new_prospects():
            if not self.limiter.can_send_connection_request():
                logger.info(f"[{self.name}] Connection request limit reached.")
                break
            if not self.is_in_time_window():
                break

            try:
                note = self.messages.render_connection_note(prospect)
                success = self.client.send_connection_request(prospect.public_id, note)
                if success:
                    self.store.mark_connection_sent(prospect.public_id)
                    if f"account:{self.name}" not in prospect.tags:
                        prospect.tags.append(f"account:{self.name}")
                    self.store.save()
                    self.limiter.record_connection_request()
                    summary["connection_requests_sent"] += 1
                else:
                    self.store.update_status(prospect.public_id, "failed")
                    summary["errors"] += 1
            except Exception as e:
                logger.error(f"[{self.name}] Error sending connection to {prospect.full_name}: {e}")
                summary["errors"] += 1

        logger.info(f"[{self.name}] --- Checking pending connections ---")
        for prospect in self._get_my_pending():
            if not self.limiter.can_view_profile():
                break

            try:
                status = self.client.check_connection_status(prospect.public_id)
                self.limiter.record_profile_view()
                if status == "connected":
                    self.store.mark_connected(prospect.public_id)
                    summary["connections_accepted"] += 1
            except Exception as e:
                logger.error(f"[{self.name}] Error checking {prospect.full_name}: {e}")

        logger.info(f"[{self.name}] --- Sending follow-ups ---")
        candidates = self.store.get_needing_followup(
            max_followups=self.config.messages.max_followups,
            min_days=self.config.messages.followup_delay_days,
        )
        for prospect in candidates:
            if f"account:{self.name}" not in prospect.tags:
                continue
            if not self.limiter.can_send_message():
                break
            if not self.is_in_time_window():
                break

            idx = prospect.followups_sent
            try:
                msg = self.messages.render_followup(prospect, idx)
                if not msg:
                    continue
                success = self.client.send_message(prospect.public_id, msg)
                if success:
                    self.store.mark_followup_sent(prospect.public_id)
                    self.limiter.record_message()
                    summary["followups_sent"] += 1
                else:
                    summary["errors"] += 1
            except Exception as e:
                logger.error(f"[{self.name}] Error follow-up to {prospect.full_name}: {e}")
                summary["errors"] += 1

        logger.info(f"[{self.name}] Cycle done: {summary}")
        return summary

    def _get_my_new_prospects(self) -> list[Prospect]:
        """Get new prospects that haven't been claimed by another account."""
        new = self.store.get_new_prospects()
        mine = []
        for p in new:
            account_tags = [t for t in p.tags if t.startswith("account:")]
            if not account_tags or f"account:{self.name}" in account_tags:
                mine.append(p)
        return mine

    def _get_my_pending(self) -> list[Prospect]:
        pending = self.store.get_pending_connections()
        return [p for p in pending if f"account:{self.name}" in p.tags]

    def get_stats(self) -> dict:
        return self.limiter.today_stats()


class MultiAccountManager:
    """
    Coordinates multiple AccountWorkers, running them sequentially
    with staggered timing so they don't overlap.
    """

    def __init__(self, config: CampaignConfig):
        self.config = config

        self.global_store = ProspectStore(config.data_dir, config.campaign_name)

        self.workers: list[AccountWorker] = []
        for account in config.accounts:
            worker = AccountWorker(account, config, self.global_store)
            self.workers.append(worker)

        logger.info(
            f"Multi-account manager initialized with {len(self.workers)} accounts: "
            f"{[w.name for w in self.workers]}"
        )

    def connect_all(self) -> dict[str, bool]:
        results = {}
        for worker in self.workers:
            success = worker.connect()
            results[worker.name] = success
            if success:
                gap = random.uniform(10, 30)
                logger.info(f"Waiting {gap:.0f}s before connecting next account...")
                time.sleep(gap)
        return results

    def run_cycle(self) -> list[dict]:
        """Run one cycle across all accounts, sequentially with gaps."""
        random.shuffle(self.workers)

        summaries = []
        for worker in self.workers:
            if not worker.is_connected:
                logger.warning(f"[{worker.name}] Skipping (not connected).")
                continue

            summary = worker.run_cycle()
            summaries.append(summary)

            if not summary.get("skipped"):
                gap = random.uniform(120, 600)
                logger.info(f"Inter-account gap: sleeping {gap:.0f}s before next account...")
                time.sleep(gap)

        return summaries

    def run_continuous(self, cycles: int = 0) -> None:
        count = 0
        while cycles == 0 or count < cycles:
            count += 1
            logger.info(f"=== Multi-account cycle {count} ===")
            summaries = self.run_cycle()

            active = sum(1 for s in summaries if not s.get("skipped"))
            if active == 0:
                logger.info("No accounts active this window. Sleeping 30 minutes...")
                time.sleep(1800)
            else:
                sleep_min = random.randint(30, 90)
                logger.info(f"Cycle complete. Sleeping {sleep_min} minutes...")
                time.sleep(sleep_min * 60)

    def get_stats(self) -> dict:
        prospect_stats = self.global_store.stats()
        account_stats = {}
        for w in self.workers:
            account_stats[w.name] = {
                "connected": w.is_connected,
                "segment": w.account.segment,
                "time_window": f"{w.account.start_hour}:00-{w.account.end_hour}:00",
                "proxy": "yes" if w.account.proxy else "no",
                "today": w.get_stats(),
            }
        return {
            "campaign": self.config.campaign_name,
            "total_accounts": len(self.workers),
            "prospects": prospect_stats,
            "accounts": account_stats,
        }
