"""
Prospect finder - searches LinkedIn and filters results into qualified prospects.
"""

import logging
from typing import Optional

from .config import SearchCriteria
from .linkedin_client import LinkedInClient
from .prospect_store import Prospect, ProspectStore

logger = logging.getLogger(__name__)

NETWORK_DEPTH_MAP = {
    "1st": ["F"],
    "2nd": ["S"],
    "3rd": ["O"],
    "2nd+3rd": ["S", "O"],
}


class ProspectFinder:
    def __init__(
        self,
        client: LinkedInClient,
        store: ProspectStore,
        criteria: SearchCriteria,
    ):
        self._client = client
        self._store = store
        self._criteria = criteria

    def search_and_store(self, limit: int = 50) -> list[Prospect]:
        """
        Run LinkedIn search based on configured criteria,
        filter results, enrich with profile data, and store new prospects.
        """
        network_depths = NETWORK_DEPTH_MAP.get(
            self._criteria.connection_degree, ["S"]
        )

        all_results = []
        for title in self._criteria.job_titles:
            results = self._client.search_people(
                keyword_title=title,
                network_depths=network_depths,
                regions=self._criteria.locations or None,
                industries=self._criteria.industries or None,
                limit=limit,
            )
            all_results.extend(results)

        if self._criteria.keywords:
            kw_str = " ".join(self._criteria.keywords)
            results = self._client.search_people(
                keywords=kw_str,
                network_depths=network_depths,
                regions=self._criteria.locations or None,
                industries=self._criteria.industries or None,
                limit=limit,
            )
            all_results.extend(results)

        seen_ids = set()
        unique = []
        for r in all_results:
            pid = r.get("public_id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique.append(r)

        logger.info(f"De-duplicated to {len(unique)} unique results.")

        new_prospects = []
        for result in unique:
            pid = result.get("public_id", "")
            if not pid:
                continue

            if self._store.get(pid):
                logger.debug(f"Skipping already-known prospect: {pid}")
                continue

            if self._should_exclude(result):
                logger.debug(f"Excluding prospect: {pid}")
                continue

            prospect = self._enrich_result(result)
            if prospect and self._store.add(prospect):
                new_prospects.append(prospect)
                logger.info(f"Added new prospect: {prospect.full_name} ({prospect.job_title} at {prospect.company})")

        logger.info(f"Found {len(new_prospects)} new qualified prospects.")
        return new_prospects

    def _should_exclude(self, result: dict) -> bool:
        headline = (result.get("headline") or result.get("summary") or "").lower()
        name = f"{result.get('first_name', '')} {result.get('last_name', '')}".lower()
        combined = f"{headline} {name}"

        for kw in self._criteria.exclude_keywords:
            if kw.lower() in combined:
                return True
        return False

    def _enrich_result(self, result: dict) -> Optional[Prospect]:
        """Fetch full profile data to build a rich Prospect record."""
        pid = result.get("public_id", "")
        try:
            profile = self._client.get_profile(pid)
        except Exception as e:
            logger.warning(f"Could not enrich profile {pid}: {e}")
            profile = result

        first_name = profile.get("firstName", result.get("first_name", ""))
        last_name = profile.get("lastName", result.get("last_name", ""))

        job_title = ""
        company = ""
        industry = profile.get("industryName", "")

        experience = profile.get("experience", [])
        if experience:
            current = experience[0]
            job_title = current.get("title", "")
            company = current.get("companyName", "")

        if not job_title:
            job_title = profile.get("headline", result.get("headline", ""))

        location = profile.get("locationName", profile.get("geoLocationName", ""))

        return Prospect(
            public_id=pid,
            first_name=first_name,
            last_name=last_name,
            headline=profile.get("headline", ""),
            job_title=job_title,
            company=company,
            industry=industry,
            location=location,
            mutual_connections=result.get("sharedConnectionsCount", 0),
            profile_url=f"https://www.linkedin.com/in/{pid}/",
        )
