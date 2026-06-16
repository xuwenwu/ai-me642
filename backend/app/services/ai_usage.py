from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import Settings
from ..models import PromptLogEntry


@dataclass
class AIUsage:
    request_limit: int
    requests_used: int
    token_budget: int
    tokens_estimated: int

    @property
    def remaining_requests(self) -> int:
        return max(self.request_limit - self.requests_used, 0)

    @property
    def remaining_tokens(self) -> int:
        return max(self.token_budget - self.tokens_estimated, 0)


def estimate_tokens(text: str) -> int:
    return max((len(text or "") + 3) // 4, 1)


def month_start(now: datetime | None = None) -> datetime:
    current = now or datetime.now()
    return current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def monthly_external_usage(db: Session, settings: Settings) -> AIUsage:
    rows = (
        db.query(PromptLogEntry)
        .filter(
            PromptLogEntry.provider_status == "generated_external",
            PromptLogEntry.created_at >= month_start(),
        )
        .all()
    )
    tokens = sum(estimate_tokens(row.prompt_text) + estimate_tokens(row.ai_output_summary) for row in rows)
    return AIUsage(
        request_limit=max(settings.ai_monthly_external_request_limit, 0),
        requests_used=len(rows),
        token_budget=max(settings.ai_monthly_token_budget, 0),
        tokens_estimated=tokens,
    )


def assert_external_budget_available(db: Session, settings: Settings, prompt_text: str) -> None:
    usage = monthly_external_usage(db, settings)
    if usage.request_limit and usage.requests_used >= usage.request_limit:
        raise RuntimeError("Monthly external AI request limit has been reached.")
    projected_tokens = usage.tokens_estimated + estimate_tokens(prompt_text) + settings.ai_external_max_output_tokens
    if usage.token_budget and projected_tokens > usage.token_budget:
        raise RuntimeError("Monthly external AI token budget would be exceeded.")
