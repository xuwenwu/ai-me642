from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Callable

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
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


PRIVACY_PATTERNS = [
    ("possible email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("possible api key", re.compile(r"\b(?:api[_-]?key|secret|token|password)\s*[:=]", re.IGNORECASE)),
    ("possible bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE)),
    ("possible openai key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("possible private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("possible ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
ALLOWED_REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh"}
ALLOWED_VERBOSITY = {"low", "medium", "high"}

COURSE_ASSISTANT_SCHEMA: dict[str, Any] = {
    "type": "json_schema",
    "name": "me642_course_assistant_guidance",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "guidance_summary": {"type": "string"},
            "suggested_checks": {"type": "array", "items": {"type": "string"}},
            "caution_flags": {"type": "array", "items": {"type": "string"}},
            "student_next_steps": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["guidance_summary", "suggested_checks", "caution_flags", "student_next_steps"],
    },
}

HttpPost = Callable[..., httpx.Response]


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


def _system_prompt(policy: AIPolicy) -> str:
    base = policy.assistant_system_prompt.strip() or (
        "You are a cautious ME642 course assistant. Help students plan checks, debug reasoning, "
        "and interpret validation evidence. Do not fabricate simulation outputs, grades, or final scientific claims."
    )
    return (
        f"{base}\n\n"
        "Production rules:\n"
        "- Give bounded guidance for scientific computing coursework.\n"
        "- Do not grade the student or claim the simulation is correct without evidence.\n"
        "- Ask the student to verify against uploaded files, validation checks, and thermo plots.\n"
        "- Keep advice concise, auditable, and suitable for a prompt log.\n"
        "- Never request secrets, credentials, personal data, or private course records."
    )


def _user_prompt(task_type: str, prompt_text: str) -> str:
    return (
        f"Task type: {task_type.strip() or 'lammps_debugging'}\n\n"
        "Student/instructor request:\n"
        f"{prompt_text.strip()}\n\n"
        "Return guidance that helps the student decide what evidence to inspect next. "
        "Focus on validation checks, thermo trends, warnings, reproducibility, AI disclosure, and remaining uncertainty."
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


def _extract_usage(payload: dict) -> tuple[int, int, int]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
    return input_tokens, output_tokens, total_tokens


def _structured_guidance_text(raw_text: str) -> str:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text
    if not isinstance(data, dict):
        return raw_text

    sections = [
        ("Guidance", data.get("guidance_summary")),
        ("Suggested checks", data.get("suggested_checks")),
        ("Caution flags", data.get("caution_flags")),
        ("Student next steps", data.get("student_next_steps")),
    ]
    lines: list[str] = []
    for title, value in sections:
        if isinstance(value, str) and value.strip():
            lines.append(f"{title}: {value.strip()}")
        elif isinstance(value, list) and value:
            lines.append(f"{title}:")
            for item in value:
                if str(item).strip():
                    lines.append(f"- {str(item).strip()}")
    return "\n".join(lines).strip() or raw_text


def _openai_request_body(settings: Settings, policy: AIPolicy, task_type: str, prompt_text: str, model: str) -> dict[str, Any]:
    reasoning_effort = settings.ai_reasoning_effort.strip().lower()
    verbosity = settings.ai_text_verbosity.strip().lower()
    body: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": _system_prompt(policy)},
            {"role": "user", "content": _user_prompt(task_type, prompt_text)},
        ],
        "store": False,
        "max_output_tokens": settings.ai_external_max_output_tokens,
        "text": {
            "format": COURSE_ASSISTANT_SCHEMA,
            "verbosity": verbosity if verbosity in ALLOWED_VERBOSITY else "low",
        },
    }
    if reasoning_effort in ALLOWED_REASONING_EFFORTS:
        body["reasoning"] = {"effort": reasoning_effort}
    return body


def run_course_assistant(
    settings: Settings,
    policy: AIPolicy,
    task_type: str,
    prompt_text: str,
    force_enabled: bool = False,
    post_response: HttpPost | None = None,
) -> AIProviderResult:
    if not force_enabled and not policy.assistant_enabled:
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

    post = post_response or httpx.post
    try:
        response = post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=_openai_request_body(settings, policy, task_type, prompt_text, model),
            timeout=settings.ai_provider_timeout_seconds,
        )
    except httpx.TimeoutException as exc:
        raise AIProviderError("AI provider request timed out.") from exc
    except httpx.RequestError as exc:
        raise AIProviderError("AI provider request could not be completed.") from exc
    if response.status_code >= 400:
        detail = ""
        try:
            error = response.json().get("error", {})
            if isinstance(error, dict):
                detail = str(error.get("message") or "")
        except Exception:
            detail = response.text[:200]
        suffix = f" {detail}" if detail else ""
        raise AIProviderError(f"AI provider request failed with status {response.status_code}.{suffix}")
    payload = response.json()
    output = _structured_guidance_text(_extract_response_text(payload))
    if not output:
        raise AIProviderError("AI provider returned an empty response.")
    input_tokens, output_tokens, total_tokens = _extract_usage(payload)
    return AIProviderResult(
        output_summary=output,
        provider_status="generated_external",
        provider_model=model,
        provider_response_id=str(payload.get("id") or ""),
        privacy_flags=flags,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )
