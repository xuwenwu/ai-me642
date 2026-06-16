import json

import httpx
import pytest

from app.config import Settings
from app.models import AIPolicy
from app.services.ai_provider import AIPrivacyBlocked, OPENAI_RESPONSES_URL, run_course_assistant


def _settings() -> Settings:
    return Settings(
        ai_provider_enabled=True,
        ai_provider_mode="openai",
        ai_provider_model="gpt-5.4-mini",
        ai_external_max_output_tokens=300,
        ai_reasoning_effort="low",
        ai_text_verbosity="low",
        openai_api_key="sk-test12345678901234567890",
    )


def _policy() -> AIPolicy:
    return AIPolicy(
        course_id=1,
        assistant_enabled=True,
        assistant_provider="openai",
        assistant_model="gpt-5.4-mini",
        assistant_system_prompt="You are a cautious course assistant.",
    )


def test_openai_provider_uses_structured_responses_and_records_usage():
    captured: dict = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "id": "resp_test_123",
                "output_text": json_module.dumps(
                    {
                        "guidance_summary": "Inspect energy drift before making an NVE stability claim.",
                        "suggested_checks": ["Check TotEng trend", "Read LAMMPS warnings"],
                        "caution_flags": ["Do not treat validation as a grade"],
                        "student_next_steps": ["Save interpretation after reviewing plots"],
                    }
                ),
                "usage": {"input_tokens": 120, "output_tokens": 45, "total_tokens": 165},
            },
        )

    json_module = json
    result = run_course_assistant(
        _settings(),
        _policy(),
        "lammps_debugging",
        "Help me interpret an NVE validation warning.",
        post_response=fake_post,
    )

    assert captured["url"] == OPENAI_RESPONSES_URL
    assert captured["headers"]["Authorization"].startswith("Bearer sk-test")
    assert captured["json"]["store"] is False
    assert captured["json"]["model"] == "gpt-5.4-mini"
    assert captured["json"]["reasoning"] == {"effort": "low"}
    assert captured["json"]["text"]["verbosity"] == "low"
    assert captured["json"]["text"]["format"]["type"] == "json_schema"
    assert "validation checks" in captured["json"]["input"][1]["content"]
    assert result.provider_status == "generated_external"
    assert result.provider_response_id == "resp_test_123"
    assert result.input_tokens == 120
    assert result.output_tokens == 45
    assert result.total_tokens == 165
    assert "Guidance: Inspect energy drift" in result.output_summary
    assert "- Check TotEng trend" in result.output_summary


def test_openai_provider_blocks_private_prompt_before_external_call():
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    with pytest.raises(AIPrivacyBlocked):
        run_course_assistant(
            _settings(),
            _policy(),
            "lammps_debugging",
            "Help me with student@example.edu and password=temporary-pass-123.",
            post_response=fake_post,
        )

    assert called is False
