"""
Campaign manager - orchestrates the full outreach workflow:
  1. Find prospects
  2. Send connection requests
  3. Check for accepted connections
  4. Send follow-up messages
  5. Track everything
"""

import logging
import time
import random
from pathlib import Path
from datetime import datetime

from .config import CampaignConfig, load_config
from .linkedin_client import LinkedInClient
from .prospect_store import (
    ProspectStore,
    Prospect,
    STATUS_NEW,
    STATUS_REQUEST_SENT,
    STATUS_CONNECTED,
)
from .prospect_finder import ProspectFinder
from .message_engine import MessageEngine
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class Campaign:
    def __init__(self, config: CampaignConfig):
        self.config = config
        self.client = LinkedInClient(config.credentials, config.rate_limits)
        self.store = ProspectStore(config.data_dir, config.campaign_name)
        self.finder = ProspectFinder(self.client, self.store, config.search)
        self.limiter = RateLimiter(config.rate_limits, config.data_dir, config.campaign_name)
        self.messages = MessageEngine(config.messages)
        self._your_name = ""

    def start(self) -> None:
        logger.info(f"Starting campaign: {self.config.campaign_name}")
        self.client.connect()

        try:
            own = self.client.get_own_profile()
            self._your_name = f"{own.get('firstName', '')} {own.get('lastName', '')}".strip()
            self.messages._your_name = self._your_name
            logger.info(f"Running as: {self._your_name}")
        except Exception as e:
            logger.warning(f"Could not fetch own profile: {e}")

    def run_cycle(self) -> dict:
        """
        Execute one full outreach cycle:
          - Search for new prospects
          - Send connection requests to new prospects
          - Check pending connections for acceptance
          - Send follow-ups to connected prospects
        Returns a summary dict.
        """
        summary = {
            "prospects_found": 0,
            "connection_requests_sent": 0,
            "connections_accepted": 0,
            "followups_sent": 0,
            "errors": 0,
        }

        self.limiter.wait_until_working_hours()

        logger.info("--- Phase 1: Searching for new prospects ---")
        try:
            new_prospects = self.finder.search_and_store(limit=30)
            summary["prospects_found"] = len(new_prospects)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            summary["errors"] += 1

        logger.info("--- Phase 2: Sending connection requests ---")
        for prospect in self.store.get_new_prospects():
            if not self.limiter.can_send_connection_request():
                logger.info("Connection request limit reached for today.")
                break
            if not self.limiter.is_within_working_hours():
                logger.info("Outside working hours, stopping connections.")
                break

            try:
                note = self.messages.render_connection_note(prospect)
                success = self.client.send_connection_request(prospect.public_id, note)
                if success:
                    self.store.mark_connection_sent(prospect.public_id)
                    self.limiter.record_connection_request()
                    summary["connection_requests_sent"] += 1
                    logger.info(f"Sent connection request to {prospect.full_name}")
                else:
                    self.store.update_status(prospect.public_id, "failed")
                    summary["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending connection to {prospect.full_name}: {e}")
                summary["errors"] += 1

        logger.info("--- Phase 3: Checking pending connections ---")
        for prospect in self.store.get_pending_connections():
            if not self.limiter.can_view_profile():
                break

            try:
                status = self.client.check_connection_status(prospect.public_id)
                self.limiter.record_profile_view()
                if status == "connected":
                    self.store.mark_connected(prospect.public_id)
                    summary["connections_accepted"] += 1
                    logger.info(f"{prospect.full_name} accepted connection!")
            except Exception as e:
                logger.error(f"Error checking connection for {prospect.full_name}: {e}")

        logger.info("--- Phase 4: Sending follow-ups ---")
        followup_candidates = self.store.get_needing_followup(
            max_followups=self.config.messages.max_followups,
            min_days=self.config.messages.followup_delay_days,
        )
        for prospect in followup_candidates:
            if not self.limiter.can_send_message():
                logger.info("Message limit reached for today.")
                break
            if not self.limiter.is_within_working_hours():
                break

            idx = prospect.followups_sent
            delay = self.messages.get_followup_delay_days(idx)

            ref_str = prospect.last_followup_at or prospect.connected_at
            if ref_str:
                ref = datetime.fromisoformat(ref_str)
                if (datetime.utcnow() - ref).days < delay:
                    continue

            try:
                msg = self.messages.render_followup(prospect, idx)
                if not msg:
                    continue
                success = self.client.send_message(prospect.public_id, msg)
                if success:
                    self.store.mark_followup_sent(prospect.public_id)
                    self.limiter.record_message()
                    summary["followups_sent"] += 1
                    logger.info(f"Sent follow-up #{idx + 1} to {prospect.full_name}")
                else:
                    summary["errors"] += 1
            except Exception as e:
                logger.error(f"Error sending follow-up to {prospect.full_name}: {e}")
                summary["errors"] += 1

        logger.info(f"Cycle complete: {summary}")
        return summary

    def run_continuous(self, cycles: int = 0) -> None:
        """
        Run cycles continuously. If cycles=0, run indefinitely.
        Between cycles, sleep until the next working period.
        """
        count = 0
        while cycles == 0 or count < cycles:
            count += 1
            logger.info(f"=== Cycle {count} ===")
            summary = self.run_cycle()

            sleep_min = random.randint(30, 90)
            logger.info(f"Sleeping {sleep_min} minutes before next cycle...")
            time.sleep(sleep_min * 60)

    def print_stats(self) -> dict:
        prospect_stats = self.store.stats()
        limiter_stats = self.limiter.today_stats()
        return {
            "campaign": self.config.campaign_name,
            "prospects": prospect_stats,
            "today_usage": limiter_stats,
        }
