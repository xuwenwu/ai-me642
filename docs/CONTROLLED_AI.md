# Controlled AI Integration

Phase X adds an optional course assistant path for prompt-log workflows. It is disabled by default and designed for instructor-controlled pilots.

## Default Mode

The default provider is `offline`. It does not call an external model. It creates deterministic course-guidance text and records it as a normal prompt log with provider metadata.

## External Provider Mode

External provider calls require both:

1. Instructor policy enables the course assistant in Course Setup.
2. Server environment enables provider calls:

```powershell
AI_PROVIDER_ENABLED=true
AI_PROVIDER_MODE=openai
AI_PROVIDER_MODEL=gpt-5.4-mini
AI_EXTERNAL_MAX_OUTPUT_TOKENS=700
AI_REASONING_EFFORT=low
AI_TEXT_VERBOSITY=low
AI_PROVIDER_TIMEOUT_SECONDS=30
AI_MONTHLY_EXTERNAL_REQUEST_LIMIT=200
AI_MONTHLY_TOKEN_BUDGET=200000
OPENAI_API_KEY=<server-side-key>
```

Use `gpt-5.4-mini` for the first course pilot unless there is a specific need for the higher-cost `gpt-5.5` model. The course assistant is designed for bounded guidance, not unrestricted tutoring or grading.

The backend sends OpenAI requests through the Responses API with `store=false`, a structured JSON output contract, low reasoning effort by default, and concise verbosity. The structured response is converted into a student-readable prompt-log summary.

The backend blocks external calls if the prompt appears to include private email addresses, API keys, passwords, bearer tokens, OpenAI-style keys, US SSNs, or private-key material. These checks are conservative hints, not a complete data-loss-prevention system.

Course Setup includes an instructor-only readiness panel and test button. Use it before enabling the assistant for students. The test path verifies provider configuration without exposing the API key to the browser.

External calls also respect monthly request and token guardrails. When OpenAI returns usage metadata, the app stores actual input/output/total token counts on the generated prompt log; otherwise it falls back to conservative estimates. Offline course guidance does not count against these limits.

## Logged Metadata

Generated prompt logs store:

- provider status
- provider model
- provider response id, when available
- provider input, output, and total token counts when available
- privacy flags
- prompt text
- AI output summary

Students still need to fill accepted parts, rejected parts, manual edits, validation performed, and remaining concerns before using AI assistance as submission evidence.

## Pilot Review

For a private class pilot, start with `offline` mode. Only enable external provider mode after confirming course policy, FERPA/privacy expectations, API billing ownership, and institutional approval.
