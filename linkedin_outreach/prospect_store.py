"""
Prospect data store - tracks all prospects and their outreach status.
Uses a simple JSON file as the database for portability.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

STATUS_NEW = "new"
STATUS_VIEWED = "viewed"
STATUS_REQUEST_SENT = "connection_request_sent"
STATUS_CONNECTED = "connected"
STATUS_FOLLOWUP_1 = "followup_1_sent"
STATUS_FOLLOWUP_2 = "followup_2_sent"
STATUS_REPLIED = "replied"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


@dataclass
class Prospect:
    public_id: str
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    job_title: str = ""
    company: str = ""
    industry: str = ""
    location: str = ""
    mutual_connections: int = 0
    profile_url: str = ""
    status: str = STATUS_NEW
    connection_request_sent_at: Optional[str] = None
    connected_at: Optional[str] = None
    followups_sent: int = 0
    last_followup_at: Optional[str] = None
    last_action_at: Optional[str] = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class ProspectStore:
    """Persistent prospect tracker backed by a JSON file."""

    def __init__(self, data_dir: str, campaign_name: str):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / f"{campaign_name}_prospects.json"
        self._prospects: dict[str, Prospect] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            with open(self._path, "r") as f:
                raw = json.load(f)
            for pid, data in raw.items():
                self._prospects[pid] = Prospect(**data)
            logger.info(f"Loaded {len(self._prospects)} prospects from {self._path}")
        else:
            logger.info(f"No existing prospect file at {self._path}, starting fresh.")

    def save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(
                {pid: asdict(p) for pid, p in self._prospects.items()},
                f,
                indent=2,
                default=str,
            )

    def add(self, prospect: Prospect) -> bool:
        if prospect.public_id in self._prospects:
            return False
        self._prospects[prospect.public_id] = prospect
        self.save()
        return True

    def get(self, public_id: str) -> Optional[Prospect]:
        return self._prospects.get(public_id)

    def update_status(self, public_id: str, status: str) -> None:
        p = self._prospects.get(public_id)
        if p:
            p.status = status
            p.last_action_at = datetime.utcnow().isoformat()
            self.save()

    def mark_connection_sent(self, public_id: str) -> None:
        p = self._prospects.get(public_id)
        if p:
            p.status = STATUS_REQUEST_SENT
            p.connection_request_sent_at = datetime.utcnow().isoformat()
            p.last_action_at = datetime.utcnow().isoformat()
            self.save()

    def mark_connected(self, public_id: str) -> None:
        p = self._prospects.get(public_id)
        if p:
            p.status = STATUS_CONNECTED
            p.connected_at = datetime.utcnow().isoformat()
            p.last_action_at = datetime.utcnow().isoformat()
            self.save()

    def mark_followup_sent(self, public_id: str) -> None:
        p = self._prospects.get(public_id)
        if p:
            p.followups_sent += 1
            p.status = f"followup_{p.followups_sent}_sent"
            p.last_followup_at = datetime.utcnow().isoformat()
            p.last_action_at = datetime.utcnow().isoformat()
            self.save()

    def get_by_status(self, status: str) -> list[Prospect]:
        return [p for p in self._prospects.values() if p.status == status]

    def get_pending_connections(self) -> list[Prospect]:
        return self.get_by_status(STATUS_REQUEST_SENT)

    def get_needing_followup(self, max_followups: int, min_days: int) -> list[Prospect]:
        from datetime import timedelta

        now = datetime.utcnow()
        results = []
        for p in self._prospects.values():
            if p.status == STATUS_REPLIED or p.status == STATUS_SKIPPED:
                continue
            if p.followups_sent >= max_followups:
                continue
            if p.status not in (STATUS_CONNECTED, STATUS_FOLLOWUP_1):
                continue
            ref_time_str = p.last_followup_at or p.connected_at
            if not ref_time_str:
                continue
            ref_time = datetime.fromisoformat(ref_time_str)
            if now - ref_time >= timedelta(days=min_days):
                results.append(p)
        return results

    def get_new_prospects(self) -> list[Prospect]:
        return self.get_by_status(STATUS_NEW)

    @property
    def all_prospects(self) -> list[Prospect]:
        return list(self._prospects.values())

    def stats(self) -> dict[str, int]:
        from collections import Counter
        counts = Counter(p.status for p in self._prospects.values())
        counts["total"] = len(self._prospects)
        return dict(counts)
