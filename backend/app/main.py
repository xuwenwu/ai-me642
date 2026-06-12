from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .config import get_settings, validate_runtime_security
from .database import SessionLocal, init_db
from .routers import assignments, auth, instructor, projects, prompt_logs, submissions, validation
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


app.include_router(auth.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(prompt_logs.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(instructor.router, prefix="/api")
