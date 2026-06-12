from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..deps import current_user, ensure_owner_or_staff
from ..models import AIPolicy, Course, PromptLogEntry, PromptTemplate, User
from ..schemas import AIPolicyOut, AssistantPromptIn, PromptLogIn, PromptLogOut, PromptTemplateOut
from ..services.ai_provider import AIPrivacyBlocked, AIProviderDisabled, AIProviderError, privacy_flags, run_course_assistant


router = APIRouter(prefix="/prompt-logs", tags=["prompt-logs"])


DEFAULT_POLICY_REQUIREMENTS = [
    "Record the AI tool, task purpose, and prompt or prompt summary.",
    "Summarize the AI output in your own words.",
    "Identify accepted and rejected suggestions.",
    "Describe manual edits and validation performed after AI assistance.",
    "State remaining concerns or uncertainties before submission.",
]


def _default_course(db: Session) -> Course:
    course = db.query(Course).filter_by(code="ME642").first() or db.query(Course).order_by(Course.id).first()
    if not course:
        course = Course(code="ME642", title="Materials Modeling", term="Spring 2026")
        db.add(course)
        db.flush()
    return course


def _ensure_policy(db: Session) -> AIPolicy:
    course = _default_course(db)
    policy = db.query(AIPolicy).filter_by(course_id=course.id).first()
    if not policy:
        policy = AIPolicy(
            course_id=course.id,
            title="ME642 Responsible AI Use Policy",
            body="AI assistance is allowed when students disclose the work, verify outputs, and keep responsibility for final scientific claims.",
            disclosure_requirements_json=json.dumps(DEFAULT_POLICY_REQUIREMENTS),
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def _policy_out(policy: AIPolicy) -> AIPolicyOut:
    return AIPolicyOut(
        id=policy.id,
        course_id=policy.course_id,
        title=policy.title,
        body=policy.body,
        allowed_tools=policy.allowed_tools,
        disclosure_requirements=policy.disclosure_requirements,
        assistant_enabled=policy.assistant_enabled,
        assistant_provider=policy.assistant_provider,
        assistant_model=policy.assistant_model,
        assistant_system_prompt=policy.assistant_system_prompt,
        assistant_retention_days=policy.assistant_retention_days,
        updated_at=policy.updated_at,
    )


def _template_out(template: PromptTemplate) -> PromptTemplateOut:
    return PromptTemplateOut(
        id=template.id,
        course_id=template.course_id,
        title=template.title,
        task_type=template.task_type,
        prompt_text=template.prompt_text,
        checklist=template.checklist,
        status=template.status,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/policy", response_model=AIPolicyOut)
def ai_policy(
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> AIPolicyOut:
    return _policy_out(_ensure_policy(db))


@router.get("/templates", response_model=list[PromptTemplateOut])
def prompt_templates(
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> list[PromptTemplateOut]:
    course = _default_course(db)
    rows = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.course_id == course.id, PromptTemplate.status == "active")
        .order_by(PromptTemplate.task_type, PromptTemplate.title)
        .all()
    )
    return [_template_out(row) for row in rows]


@router.get("", response_model=list[PromptLogOut])
def list_prompt_logs(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[PromptLogEntry]:
    query = db.query(PromptLogEntry)
    if user.role not in {"instructor", "ta"}:
        query = query.filter_by(user_id=user.id)
    return query.order_by(PromptLogEntry.created_at.desc()).all()


@router.post("", response_model=PromptLogOut)
def create_prompt_log(
    payload: PromptLogIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PromptLogEntry:
    data = payload.model_dump()
    data.pop("privacy_flags", None)
    data["provider_status"] = "manual"
    data["provider_model"] = ""
    data["provider_response_id"] = ""
    prompt = PromptLogEntry(**data, privacy_flags_json=json.dumps(privacy_flags(payload.prompt_text)), user_id=user.id)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/assistant", response_model=PromptLogOut)
def generate_assistant_prompt_log(
    payload: AssistantPromptIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PromptLogEntry:
    policy = _ensure_policy(db)
    try:
        result = run_course_assistant(get_settings(), policy, payload.task_type, payload.prompt_text)
    except AIPrivacyBlocked as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderDisabled as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    prompt = PromptLogEntry(
        user_id=user.id,
        project_id=payload.project_id,
        assignment_id=payload.assignment_id,
        title=payload.title.strip(),
        ai_tool_name="ME642 Course Assistant",
        task_type=payload.task_type.strip() or "lammps_debugging",
        prompt_text=payload.prompt_text,
        ai_output_summary=result.output_summary,
        accepted_parts="",
        rejected_parts="",
        manual_edits="",
        validation_performed="",
        remaining_concerns="",
        provider_status=result.provider_status,
        provider_model=result.provider_model,
        provider_response_id=result.provider_response_id,
        privacy_flags_json=json.dumps(result.privacy_flags),
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptLogOut)
def get_prompt_log(
    prompt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PromptLogEntry:
    prompt = db.get(PromptLogEntry, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt log not found")
    ensure_owner_or_staff(prompt.user_id, user)
    return prompt
