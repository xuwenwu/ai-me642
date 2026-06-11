from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import SessionLocal, init_db
from .routers import assignments, auth, instructor, projects, prompt_logs, submissions, validation
from .services.seed_data import seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
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


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "AI-ME642 backend"}


app.include_router(auth.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(prompt_logs.router, prefix="/api")
app.include_router(submissions.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(instructor.router, prefix="/api")
