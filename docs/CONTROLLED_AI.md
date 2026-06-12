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
AI_PROVIDER_MODEL=<approved-model>
OPENAI_API_KEY=<server-side-key>
```

The backend blocks external calls if the prompt appears to include private email addresses, API keys, passwords, tokens, or private-key material. These checks are conservative hints, not a complete data-loss-prevention system.

## Logged Metadata

Generated prompt logs store:

- provider status
- provider model
- provider response id, when available
- privacy flags
- prompt text
- AI output summary

Students still need to fill accepted parts, rejected parts, manual edits, validation performed, and remaining concerns before using AI assistance as submission evidence.

## Pilot Review

For a private class pilot, start with `offline` mode. Only enable external provider mode after confirming course policy, FERPA/privacy expectations, API billing ownership, and institutional approval.
