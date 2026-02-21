from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Session as SessionModel, ProblemSet

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/me/sessions")
async def get_my_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == user.id)
        .order_by(SessionModel.started_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "slug": s.slug,
            "mode": s.mode,
            "topic_tags": s.topic_tags,
            "time_taken_seconds": s.time_taken_seconds,
            "hints_used": s.hints_used,
            "passed_core_tests": s.passed_core_tests,
            "passed_edge_tests": s.passed_edge_tests,
            "confidence": s.confidence,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/me/mastery")
async def get_mastery(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.user_id == user.id,
            SessionModel.completed_at.isnot(None),
        )
    )
    sessions = result.scalars().all()

    # Aggregate per topic in Python (cross-DB compatible, no unnest needed)
    topics: dict[str, list] = {}
    for s in sessions:
        for tag in (s.topic_tags or []):
            topics.setdefault(tag, []).append(s)

    mastery = []
    for topic, topic_sessions in topics.items():
        n = len(topic_sessions)
        clean = sum(1 for s in topic_sessions if s.hints_used == 0 and s.attempts == 1)
        mastery.append({
            "topic": topic,
            "sessions_count": n,
            "avg_time_seconds": sum(s.time_taken_seconds for s in topic_sessions) / n,
            "avg_hints": sum(s.hints_used for s in topic_sessions) / n,
            "clean_solve_rate": clean / n,
            "last_solved_at": max(
                s.completed_at for s in topic_sessions if s.completed_at
            ).isoformat(),
        })

    return sorted(mastery, key=lambda x: x["clean_solve_rate"])


@router.get("/me/problemsets")
async def get_my_problem_sets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProblemSet)
        .where(ProblemSet.user_id == user.id)
        .order_by(ProblemSet.generated_at.desc())
    )
    sets = result.scalars().all()
    return [
        {"id": str(ps.id), "mode": ps.mode, "status": ps.status, "problems": ps.problems}
        for ps in sets
    ]
