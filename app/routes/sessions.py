from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Session

router = APIRouter(tags=["sessions"])


class SessionCreate(BaseModel):
    slug: str
    mode: str = "free"  # "free" | "problem_set"
    topic_tags: list[str] = []
    problem_set_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    time_taken_seconds: int = 0
    hints_used: int = 0
    hint_level_reached: int = 0
    attempts: int = 1
    passed_core_tests: bool = False
    passed_edge_tests: bool = False
    solution_time_complexity: str | None = None
    solution_space_complexity: str | None = None
    is_optimal: bool = False
    confidence: int | None = None  # 1–5


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    session = Session(
        user_id=user.id,
        problem_set_id=uuid.UUID(body.problem_set_id) if body.problem_set_id else None,
        slug=body.slug,
        mode=body.mode,
        topic_tags=body.topic_tags,
        started_at=body.started_at,
        completed_at=body.completed_at,
        time_taken_seconds=body.time_taken_seconds,
        hints_used=body.hints_used,
        hint_level_reached=body.hint_level_reached,
        attempts=body.attempts,
        passed_core_tests=body.passed_core_tests,
        passed_edge_tests=body.passed_edge_tests,
        solution_time_complexity=body.solution_time_complexity,
        solution_space_complexity=body.solution_space_complexity,
        is_optimal=body.is_optimal,
        confidence=body.confidence,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": str(session.id)}
