from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Attempt, ProblemSet

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/me/attempts")
async def get_my_attempts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Attempt)
        .where(Attempt.user_id == user.id)
        .order_by(Attempt.submitted_at.desc())
    )
    attempts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "slug": a.slug,
            "mode": a.mode,
            "problem_set_id": str(a.problem_set_id) if a.problem_set_id else None,
            "topic_tags": a.topic_tags,
            "started_at": a.started_at.isoformat(),
            "submitted_at": a.submitted_at.isoformat(),
            "submit_index": a.submit_index,
            "hints_used": a.hints_used,
            "verdict": a.verdict,
            "passed": a.passed,
            "failed": a.failed,
            "total": a.total,
            "runtime_ms": a.runtime_ms,
            "case_categories": a.case_categories,
            "confidence": a.confidence,
        }
        for a in attempts
    ]


@router.get("/me/mastery")
async def get_mastery(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attempt).where(Attempt.user_id == user.id))
    attempts = result.scalars().all()

    # Aggregate per topic in Python (cross-DB compatible, no unnest needed)
    topics: dict[str, list[Attempt]] = {}
    for a in attempts:
        for tag in (a.topic_tags or []):
            topics.setdefault(tag, []).append(a)

    mastery = []
    for topic, topic_attempts in topics.items():
        first_tries = [a for a in topic_attempts if a.submit_index == 1]
        clean = sum(1 for a in first_tries if a.verdict == "accepted" and a.hints_used == 0)
        accepted = [a for a in topic_attempts if a.verdict == "accepted"]
        n = len(accepted)
        mastery.append({
            "topic": topic,
            "attempts_count": len(topic_attempts),
            # A topic retried without a first try on record has no clean-solve signal; count it as 0.
            "clean_solve_rate": clean / len(first_tries) if first_tries else 0.0,
            "avg_time_seconds": sum(
                (a.submitted_at - a.started_at).total_seconds() for a in accepted
            ) / n if n else None,
            "avg_hints": sum(a.hints_used for a in accepted) / n if n else None,
            "last_solved_at": max(a.submitted_at for a in accepted).isoformat() if n else None,
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
        {"id": str(ps.id), "mode": ps.mode, "problems": ps.problems}
        for ps in sets
    ]
