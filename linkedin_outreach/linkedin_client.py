"""
LinkedIn API client wrapper with anti-detection measures.
Wraps the unofficial linkedin-api library with safety features.
"""

import time
import random
import logging
from typing import Optional
from linkedin_api import Linkedin

from .config import LinkedInCredentials, RateLimits

logger = logging.getLogger(__name__)


class LinkedInClient:
    """
    Thin wrapper around linkedin-api with built-in delays and jitter
    to mimic human browsing patterns.
    """

    def __init__(self, credentials: LinkedInCredentials, rate_limits: RateLimits):
        self._creds = credentials
        self._limits = rate_limits
        self._api: Optional[Linkedin] = None
        self._last_action_time = 0.0

    def connect(self) -> None:
        logger.info("Authenticating with LinkedIn...")
        self._api = Linkedin(self._creds.email, self._creds.password)
        logger.info("Authenticated successfully.")

    @property
    def api(self) -> Linkedin:
        if self._api is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._api

    def _human_delay(self) -> None:
        """Wait a randomized interval between actions to appear human."""
        elapsed = time.time() - self._last_action_time
        base = random.uniform(
            self._limits.min_delay_between_actions_sec,
            self._limits.max_delay_between_actions_sec,
        )
        jitter = random.gauss(0, base * 0.15)
        wait = max(0, base + jitter - elapsed)
        if wait > 0:
            logger.debug(f"Human delay: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_action_time = time.time()

    def search_people(
        self,
        keywords: Optional[str] = None,
        connection_of: Optional[str] = None,
        network_depths: Optional[list[str]] = None,
        regions: Optional[list[str]] = None,
        industries: Optional[list[str]] = None,
        keyword_title: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        self._human_delay()
        logger.info(f"Searching people: keywords={keywords}, title={keyword_title}, limit={limit}")
        results = self.api.search_people(
            keywords=keywords,
            connection_of=connection_of,
            network_depths=network_depths,
            regions=regions,
            industries=industries,
            keyword_title=keyword_title,
            limit=limit,
        )
        logger.info(f"Found {len(results)} search results.")
        return results

    def get_profile(self, public_id: str) -> dict:
        self._human_delay()
        logger.debug(f"Fetching profile: {public_id}")
        return self.api.get_profile(public_id)

    def get_profile_contact_info(self, public_id: str) -> dict:
        self._human_delay()
        return self.api.get_profile_contact_info(public_id)

    def send_connection_request(self, public_id: str, message: str) -> bool:
        if len(message) > 300:
            logger.warning(
                f"Connection note too long ({len(message)} chars), truncating to 300."
            )
            message = message[:297] + "..."

        self._human_delay()
        logger.info(f"Sending connection request to {public_id}")
        try:
            profile = self.api.get_profile(public_id)
            urn_id = profile.get("profile_id") or profile.get("member_urn_id")
            if not urn_id:
                urn_parts = [v for k, v in profile.items() if "urn" in k.lower()]
                urn_id = urn_parts[0] if urn_parts else public_id

            self.api.add_connection(urn_id, message=message)
            logger.info(f"Connection request sent to {public_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send connection request to {public_id}: {e}")
            return False

    def send_message(self, public_id: str, message: str) -> bool:
        self._human_delay()
        logger.info(f"Sending message to {public_id}")
        try:
            conversation = self.api.get_conversation_details(public_id)
            if conversation:
                self.api.send_message(message_body=message, conversation_urn_id=conversation.get("id"))
            else:
                profile = self.api.get_profile(public_id)
                urn_id = profile.get("profile_id") or profile.get("member_urn_id", public_id)
                self.api.send_message(message_body=message, recipients=[urn_id])
            logger.info(f"Message sent to {public_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {public_id}: {e}")
            return False

    def check_connection_status(self, public_id: str) -> str:
        """Returns 'connected', 'pending', or 'not_connected'."""
        self._human_delay()
        try:
            profile = self.api.get_profile(public_id)
            distance = profile.get("distance", {})
            if isinstance(distance, dict):
                value = distance.get("value", "")
            else:
                value = str(distance)

            if "DISTANCE_1" in str(value):
                return "connected"
            return "not_connected"
        except Exception:
            return "unknown"

    def get_own_profile(self) -> dict:
        self._human_delay()
        return self.api.get_profile("me")
