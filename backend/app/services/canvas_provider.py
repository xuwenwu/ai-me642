from __future__ import annotations

from ..config import Settings


def canvas_status(settings: Settings) -> dict:
    configured = bool(settings.canvas_base_url and settings.canvas_course_id and settings.canvas_api_token)
    if not settings.canvas_enabled:
        message = "Canvas API integration is disabled. CSV exports remain available."
    elif configured:
        message = "Canvas API integration is configured. Live sync endpoints can be enabled after institutional approval."
    else:
        message = "Canvas API integration is enabled but missing required server-side settings."
    return {
        "enabled": settings.canvas_enabled,
        "configured": configured,
        "base_url": settings.canvas_base_url.rstrip("/"),
        "course_id": settings.canvas_course_id,
        "message": message,
    }
