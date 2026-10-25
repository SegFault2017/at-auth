from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Attempt

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _topic_mastery(topic: str, attempts: list[Attempt]) -> dict:
    first_tries = [a for a in attempts if a.submit_index == 1]
    clean = [a for a in first_tries if a.verdict == "accepted" and a.hints_used == 0]
    accepted = [a for a in attempts if a.verdict == "accepted"]
    return {
        "topic": topic,
        "attempts_count": len(attempts),
        # A topic retried without a first try on record has no clean-solve signal; count it as 0.
        "clean_solve_rate": len(clean) / len(first_tries) if first_tries else 0.0,
        "avg_time_seconds": _mean([(a.submitted_at - a.started_at).total_seconds() for a in accepted]),
        "avg_hints": _mean([a.hints_used for a in accepted]),
        "last_solved_at": max(a.submitted_at for a in accepted).isoformat() if accepted else None,
    }


@router.get("/me/mastery")
async def get_mastery(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attempt).where(Attempt.user_id == user.id))

    # Aggregate per topic in Python (cross-DB compatible, no unnest needed)
    topics: dict[str, list[Attempt]] = {}
    for a in result.scalars().all():
        for tag in (a.topic_tags or []):
            topics.setdefault(tag, []).append(a)

    mastery = [_topic_mastery(topic, attempts) for topic, attempts in topics.items()]
    return sorted(mastery, key=lambda x: x["clean_solve_rate"])
