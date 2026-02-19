"""
Message personalization engine.
Renders Jinja2 templates with prospect-specific data and adds
subtle variation to avoid duplicate-message detection.
"""

import random
import logging
from jinja2 import Template

from .config import MessageConfig
from .prospect_store import Prospect

logger = logging.getLogger(__name__)

FILLER_VARIATIONS = {
    "Hi": ["Hi", "Hey", "Hello"],
    "Thanks": ["Thanks", "Thank you", "Appreciate it"],
    "great": ["great", "impressive", "excellent", "fantastic"],
    "Curious": ["Curious", "Wondering", "Interested to know"],
    "love to": ["love to", "like to", "be glad to", "be happy to"],
}


class MessageEngine:
    def __init__(self, config: MessageConfig, your_name: str = "", your_company: str = ""):
        self._config = config
        self._your_name = your_name
        self._your_company = config.your_company or your_company
        self._service = config.service

    def render_connection_note(self, prospect: Prospect) -> str:
        if not self._config.connection_note_templates:
            return ""

        template_str = random.choice(self._config.connection_note_templates)
        rendered = self._render(template_str, prospect)
        rendered = self._add_variation(rendered)

        if len(rendered) > 300:
            rendered = rendered[:297] + "..."

        return rendered.strip()

    def render_followup(self, prospect: Prospect, followup_index: int) -> str:
        templates = self._config.followup_templates
        if followup_index >= len(templates):
            return ""

        entry = templates[followup_index]
        template_str = entry.get("template", "") if isinstance(entry, dict) else str(entry)
        rendered = self._render(template_str, prospect)
        rendered = self._add_variation(rendered)
        return rendered.strip()

    def get_followup_delay_days(self, followup_index: int) -> int:
        templates = self._config.followup_templates
        if followup_index < len(templates):
            entry = templates[followup_index]
            if isinstance(entry, dict):
                return entry.get("delay_days", self._config.followup_delay_days)
        return self._config.followup_delay_days

    def _render(self, template_str: str, prospect: Prospect) -> str:
        tmpl = Template(template_str)
        mutual = prospect.mutual_connections
        mutual_text = f"{mutual}" if mutual > 0 else "several"

        return tmpl.render(
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            full_name=prospect.full_name,
            job_title=prospect.job_title,
            company=prospect.company or "your company",
            industry=prospect.industry or "your industry",
            location=prospect.location,
            mutual_count=mutual_text,
            headline=prospect.headline,
            your_name=self._your_name,
            your_company=self._your_company,
            service=self._service,
        )

    @staticmethod
    def _add_variation(text: str) -> str:
        """
        Randomly swap certain words/phrases with synonyms to make
        each message slightly unique, defeating duplicate detection.
        """
        for original, alternatives in FILLER_VARIATIONS.items():
            if original in text and random.random() < 0.4:
                replacement = random.choice(alternatives)
                text = text.replace(original, replacement, 1)
        return text
