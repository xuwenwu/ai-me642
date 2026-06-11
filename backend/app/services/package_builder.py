from __future__ import annotations
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from sqlalchemy.orm import Session
from ..models import PromptLogEntry, Submission


def build_submission_zip(db: Session, submission: Submission) -> bytes:
    prompt_logs = (
        db.query(PromptLogEntry)
        .filter(
            PromptLogEntry.user_id == submission.user_id,
            (PromptLogEntry.assignment_id == submission.assignment_id) | (PromptLogEntry.project_id == submission.project_id),
        )
        .all()
    )
    latest_report = submission.validation_reports[0] if submission.validation_reports else None
    metadata = {
        "submission_id": submission.id,
        "title": submission.title,
        "status": submission.status,
        "student_email": submission.user.email,
        "assignment": submission.assignment.title,
        "project_id": submission.project_id,
        "files": [
            {
                "id": f.id,
                "original_filename": f.original_filename,
                "file_type": f.file_type,
                "size_bytes": f.size_bytes,
                "uploaded_at": f.uploaded_at.isoformat(),
            }
            for f in submission.files
        ],
    }
    readme = [
        f"# Reproducibility Package: {submission.title}",
        "",
        f"Student: {submission.user.full_name} <{submission.user.email}>",
        f"Assignment: {submission.assignment.title}",
        "",
        "## Student Interpretation",
        submission.student_interpretation or "No interpretation recorded.",
        "",
        "## Contents",
        "- metadata.json",
        "- prompt_logs.json",
        "- validation_report.json",
        "- artifacts/",
    ]

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        zf.writestr("README.md", "\n".join(readme))
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))
        zf.writestr(
            "prompt_logs.json",
            json.dumps(
                [
                    {
                        "title": p.title,
                        "ai_tool_name": p.ai_tool_name,
                        "task_type": p.task_type,
                        "prompt_text": p.prompt_text,
                        "ai_output_summary": p.ai_output_summary,
                        "accepted_parts": p.accepted_parts,
                        "rejected_parts": p.rejected_parts,
                        "manual_edits": p.manual_edits,
                        "validation_performed": p.validation_performed,
                        "remaining_concerns": p.remaining_concerns,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in prompt_logs
                ],
                indent=2,
            ),
        )
        zf.writestr(
            "validation_report.json",
            json.dumps(
                {
                    "status": latest_report.status if latest_report else None,
                    "summary": latest_report.summary if latest_report else "No validation report recorded.",
                    "checks": [
                        {
                            "check_type": c.check_type,
                            "status": c.status,
                            "severity": c.severity,
                            "message": c.message,
                            "evidence": c.evidence,
                        }
                        for c in (latest_report.checks if latest_report else [])
                    ],
                    "thermo_series": latest_report.thermo_series if latest_report else [],
                },
                indent=2,
            ),
        )
        for artifact in submission.files:
            path = Path(artifact.file_path)
            if path.exists():
                zf.write(path, f"artifacts/{artifact.file_type}/{artifact.original_filename}")

    return buffer.getvalue()
