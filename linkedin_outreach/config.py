"""
Configuration management for LinkedIn outreach campaigns.
Loads settings from YAML config and environment variables.
Supports single-account and multi-account modes.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

CONFIG_DIR = Path(__file__).parent
DEFAULT_CONFIG_PATH = CONFIG_DIR / "campaign_config.yaml"


@dataclass
class LinkedInCredentials:
    email: str
    password: str


@dataclass
class AccountConfig:
    """Configuration for a single LinkedIn account in multi-account mode."""
    name: str
    credentials: LinkedInCredentials
    proxy: str = ""
    segment: str = ""
    job_titles: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    start_hour: int = 8
    end_hour: int = 20


@dataclass
class SearchCriteria:
    keywords: list[str] = field(default_factory=list)
    job_titles: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    company_sizes: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    connection_degree: str = "2nd"


@dataclass
class RateLimits:
    max_connection_requests_per_day: int = 20
    max_messages_per_day: int = 30
    max_profile_views_per_day: int = 80
    min_delay_between_actions_sec: int = 45
    max_delay_between_actions_sec: int = 180
    daily_start_hour: int = 8
    daily_end_hour: int = 20
    active_days: list[str] = field(
        default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri"]
    )
    warmup_enabled: bool = True
    warmup_days: int = 14
    warmup_start_pct: float = 0.2


@dataclass
class MessageConfig:
    connection_note_templates: list[str] = field(default_factory=list)
    followup_templates: list[dict] = field(default_factory=list)
    followup_delay_days: int = 3
    max_followups: int = 2
    personalize_with_profile: bool = True
    your_company: str = ""
    service: str = ""


@dataclass
class CampaignConfig:
    credentials: LinkedInCredentials
    search: SearchCriteria
    rate_limits: RateLimits
    messages: MessageConfig
    campaign_name: str = "default"
    data_dir: str = "data"
    log_dir: str = "logs"
    accounts: list[AccountConfig] = field(default_factory=list)


def _parse_account(raw: dict) -> AccountConfig:
    creds = LinkedInCredentials(
        email=raw.get("email", ""),
        password=raw.get("password", ""),
    )
    return AccountConfig(
        name=raw.get("name", creds.email.split("@")[0] if creds.email else "unnamed"),
        credentials=creds,
        proxy=raw.get("proxy", ""),
        segment=raw.get("segment", ""),
        job_titles=raw.get("job_titles", []),
        industries=raw.get("industries", []),
        locations=raw.get("locations", []),
        start_hour=raw.get("start_hour", 8),
        end_hour=raw.get("end_hour", 20),
    )


def load_config(path: Optional[str] = None) -> CampaignConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Copy campaign_config.example.yaml to campaign_config.yaml and fill in your details."
        )

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    li_email = os.environ.get("LINKEDIN_EMAIL", raw.get("credentials", {}).get("email", ""))
    li_password = os.environ.get("LINKEDIN_PASSWORD", raw.get("credentials", {}).get("password", ""))

    if not li_email or not li_password:
        if not raw.get("accounts"):
            raise ValueError(
                "LinkedIn credentials required. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD "
                "environment variables, fill them in campaign_config.yaml, or define accounts."
            )
        li_email = li_email or "multi-account-mode"
        li_password = li_password or "multi-account-mode"

    credentials = LinkedInCredentials(email=li_email, password=li_password)

    search_raw = raw.get("search", {})
    search = SearchCriteria(
        keywords=search_raw.get("keywords", []),
        job_titles=search_raw.get("job_titles", []),
        industries=search_raw.get("industries", []),
        locations=search_raw.get("locations", []),
        company_sizes=search_raw.get("company_sizes", []),
        exclude_keywords=search_raw.get("exclude_keywords", []),
        connection_degree=search_raw.get("connection_degree", "2nd"),
    )

    rl_raw = raw.get("rate_limits", {})
    rate_limits = RateLimits(
        max_connection_requests_per_day=rl_raw.get("max_connection_requests_per_day", 20),
        max_messages_per_day=rl_raw.get("max_messages_per_day", 30),
        max_profile_views_per_day=rl_raw.get("max_profile_views_per_day", 80),
        min_delay_between_actions_sec=rl_raw.get("min_delay_between_actions_sec", 45),
        max_delay_between_actions_sec=rl_raw.get("max_delay_between_actions_sec", 180),
        daily_start_hour=rl_raw.get("daily_start_hour", 8),
        daily_end_hour=rl_raw.get("daily_end_hour", 20),
        active_days=rl_raw.get("active_days", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        warmup_enabled=rl_raw.get("warmup_enabled", True),
        warmup_days=rl_raw.get("warmup_days", 14),
        warmup_start_pct=rl_raw.get("warmup_start_pct", 0.2),
    )

    msg_raw = raw.get("messages", {})
    messages = MessageConfig(
        connection_note_templates=msg_raw.get("connection_note_templates", []),
        followup_templates=msg_raw.get("followup_templates", []),
        followup_delay_days=msg_raw.get("followup_delay_days", 3),
        max_followups=msg_raw.get("max_followups", 2),
        personalize_with_profile=msg_raw.get("personalize_with_profile", True),
        your_company=msg_raw.get("your_company", ""),
        service=msg_raw.get("service", ""),
    )

    accounts = []
    for acct_raw in raw.get("accounts", []):
        accounts.append(_parse_account(acct_raw))

    return CampaignConfig(
        credentials=credentials,
        search=search,
        rate_limits=rate_limits,
        messages=messages,
        campaign_name=raw.get("campaign_name", "default"),
        data_dir=raw.get("data_dir", "data"),
        log_dir=raw.get("log_dir", "logs"),
        accounts=accounts,
    )
