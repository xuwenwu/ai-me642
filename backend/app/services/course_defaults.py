from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..models import Course, PromptTemplate


STARTER_PROMPT_TEMPLATES = [
    {
        "title": "LAMMPS debugging check",
        "task_type": "lammps_debugging",
        "prompt_text": (
            "Help me inspect this LAMMPS input/log for errors, warnings, thermo columns, physical assumptions, "
            "and missing validation evidence. Do not claim the simulation is scientifically valid unless the "
            "evidence supports it."
        ),
        "checklist": [
            "Check for fatal LAMMPS errors and warnings.",
            "Identify required thermo columns and missing outputs.",
            "Separate syntax or workflow advice from scientific conclusions.",
            "List validation steps I should perform manually.",
        ],
    },
    {
        "title": "Script generation guardrails",
        "task_type": "lammps_script",
        "prompt_text": (
            "Draft or revise a LAMMPS script for the stated material model. Include comments for assumptions, "
            "units, ensemble, timestep, boundary conditions, and outputs I must validate before submission."
        ),
        "checklist": [
            "Verify units, potential style, and atom definitions.",
            "Confirm ensemble and thermostat/barostat choices.",
            "Add reproducible thermo and dump outputs.",
            "Run a short test and inspect validation results.",
        ],
    },
    {
        "title": "Data analysis interpretation",
        "task_type": "data_analysis",
        "prompt_text": (
            "Help design an analysis plan for these MD outputs. Suggest plots, sanity checks, and caveats, "
            "but keep conclusions conditional on the actual validation evidence."
        ),
        "checklist": [
            "Choose plots that match the physical question.",
            "Check trends against expected units and ranges.",
            "Flag uncertainty, sampling limits, and equilibration concerns.",
            "Connect any conclusion to specific evidence.",
        ],
    },
    {
        "title": "Concept explanation",
        "task_type": "concept_explanation",
        "prompt_text": (
            "Explain this materials-modeling concept for ME642. Include assumptions, common mistakes, and "
            "questions I should answer before applying it to my simulation."
        ),
        "checklist": [
            "Identify assumptions and limits.",
            "Translate the concept to the assignment context.",
            "List checks that would confirm the idea in data.",
            "Note where instructor or source verification is needed.",
        ],
    },
    {
        "title": "Validation interpretation",
        "task_type": "validation_interpretation",
        "prompt_text": (
            "Help me interpret this validation report. Separate passed checks, warnings, failed checks, and "
            "scientific caveats. Keep the conclusion tied to the uploaded evidence."
        ),
        "checklist": [
            "Use validation status as advisory evidence, not a grade.",
            "Explain warnings before making a final claim.",
            "Connect thermo plots to physical expectations.",
            "State what evidence is still missing.",
        ],
    },
]


def ensure_starter_prompt_templates(db: Session, course: Course) -> int:
    created = 0
    for item in STARTER_PROMPT_TEMPLATES:
        existing = db.query(PromptTemplate).filter_by(course_id=course.id, title=item["title"]).first()
        if existing:
            continue
        db.add(
            PromptTemplate(
                course_id=course.id,
                title=item["title"],
                task_type=item["task_type"],
                prompt_text=item["prompt_text"],
                checklist_json=json.dumps(item["checklist"]),
                status="active",
            )
        )
        created += 1
    if created:
        db.flush()
    return created
