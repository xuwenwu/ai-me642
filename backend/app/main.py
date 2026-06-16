from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from .config import get_settings, validate_runtime_security
from .database import SessionLocal, init_db
from .routers import assignments, auth, feedback, instructor, projects, prompt_logs, submissions, validation
from .services.seed_data import seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    validate_runtime_security(settings)
    init_db()
    if settings.seed_demo_data:
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    yield


app = FastAPI(title="AI-ME642 Responsible Scientific Computing Studio", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    if "X-Content-Type-Options" not in response.headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
    if "X-Frame-Options" not in response.headers:
        response.headers["X-Frame-Options"] = "DENY"
    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "same-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "AI-ME642 backend", "environment": settings.app_env}


@app.get("/api/health/ready")
def readiness() -> JSONResponse:
    checks: dict[str, str] = {}
    status_code = 200

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
        status_code = 503
    finally:
        db.close()

    try:
        settings.upload_root.mkdir(parents=True, exist_ok=True)
        probe = settings.upload_root / ".healthcheck"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["upload_root"] = "ok"
    except Exception as exc:
        checks["upload_root"] = f"error: {type(exc).__name__}"
        status_code = 503

    return JSONResponse(
        {"status": "ok" if status_code == 200 else "error", "checks": checks},
        status_code=status_code,
    )


app.include_router(auth.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(prompt_logs.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(instructor.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(feedback.staff_router, prefix="/api")
