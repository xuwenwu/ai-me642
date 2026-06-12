from __future__ import annotations

from dataclasses import dataclass
import re

import httpx

from ..config import Settings
from ..models import AIPolicy


class AIProviderError(RuntimeError):
    pass


class AIProviderDisabled(AIProviderError):
    pass


class AIPrivacyBlocked(AIProviderError):
    pass


@dataclass
class AIProviderResult:
    output_summary: str
    provider_status: str
    provider_model: str
    provider_response_id: str
    privacy_flags: list[str]


PRIVACY_PATTERNS = [
    ("possible email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("possible api key", re.compile(r"\b(?:api[_-]?key|secret|token|password)\s*[:=]", re.IGNORECASE)),
    ("possible private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def privacy_flags(text: str) -> list[str]:
    flags: list[str] = []
    for label, pattern in PRIVACY_PATTERNS:
        if pattern.search(text):
            flags.append(label)
    return flags


def _offline_guidance(task_type: str, prompt_text: str, privacy: list[str]) -> str:
    trimmed = " ".join(prompt_text.split())[:360]
    flags = f" Privacy flags noticed: {', '.join(privacy)}." if privacy else ""
    return (
        f"Course assistant guidance for {task_type}: start by separating workflow help from scientific claims. "
        f"Check the assignment requirements, validation report, thermo trends, and any warnings before accepting advice. "
        f"Keep accepted suggestions, rejected suggestions, manual edits, and remaining concerns in your prompt log. "
        f"Prompt focus: {trimmed}.{flags}"
    )


def _extract_response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip()


def run_course_assistant(settings: Settings, policy: AIPolicy, task_type: str, prompt_text: str) -> AIProviderResult:
    if not policy.assistant_enabled:
        raise AIProviderDisabled("Course assistant is disabled by instructor policy.")
    if len(prompt_text) > settings.ai_max_prompt_chars:
        raise AIProviderError(f"Prompt is too long for the configured limit of {settings.ai_max_prompt_chars} characters.")

    mode = (policy.assistant_provider or settings.ai_provider_mode or "offline").strip().lower()
    model = (policy.assistant_model or settings.ai_provider_model).strip()
    flags = privacy_flags(prompt_text)

    if mode == "offline":
        return AIProviderResult(
            output_summary=_offline_guidance(task_type, prompt_text, flags),
            provider_status="generated_offline",
            provider_model="offline_course_guidance",
            provider_response_id="",
            privacy_flags=flags,
        )

    if mode != "openai":
        raise AIProviderError(f"Unsupported AI provider mode: {mode}")
    if flags:
        raise AIPrivacyBlocked("External AI request blocked because the prompt may contain private or secret data.")
    if not settings.ai_provider_enabled:
        raise AIProviderDisabled("External AI provider calls are disabled on this server.")
    if not settings.openai_api_key:
        raise AIProviderDisabled("OpenAI API key is not configured on this server.")
    if not model:
        raise AIProviderError("AI provider model is not configured.")

    response = httpx.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": [
                {"role": "system", "content": policy.assistant_system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            "store": False,
            "max_output_tokens": 700,
        },
        timeout=30,
    )
    if response.status_code >= 400:
        raise AIProviderError(f"AI provider request failed with status {response.status_code}.")
    payload = response.json()
    output = _extract_response_text(payload)
    if not output:
        raise AIProviderError("AI provider returned an empty response.")
    return AIProviderResult(
        output_summary=output,
        provider_status="generated_external",
        provider_model=model,
        provider_response_id=str(payload.get("id") or ""),
        privacy_flags=flags,
    )
