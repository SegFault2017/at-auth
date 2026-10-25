import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, ProblemSet

router = APIRouter(prefix="/problemsets", tags=["problemsets"])


class ProblemSetCreate(BaseModel):
    mode: str  # "interview_sim" | "drill"
    problems: list[dict]  # [{slug, time_limit_seconds}]


@router.post("", status_code=201)
async def create_problem_set(
    body: ProblemSetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ps = ProblemSet(
        user_id=user.id,
        mode=body.mode,
        problems=body.problems,
    )
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return {"id": str(ps.id), "mode": ps.mode, "problems": ps.problems}


@router.get("/{problem_set_id}")
async def get_problem_set(
    problem_set_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProblemSet).where(
            ProblemSet.id == uuid.UUID(problem_set_id),
            ProblemSet.user_id == user.id,
        )
    )
    ps = result.scalar_one_or_none()
    if not ps:
        raise HTTPException(status_code=404, detail="Problem set not found")
    return {"id": str(ps.id), "mode": ps.mode, "problems": ps.problems}


@router.get("")
async def list_problem_sets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProblemSet)
        .where(ProblemSet.user_id == user.id)
        .order_by(ProblemSet.generated_at.desc())
    )
    sets = result.scalars().all()
    return [
        {
            "id": str(ps.id),
            "mode": ps.mode,
            "problems": ps.problems,
            "generated_at": ps.generated_at.isoformat(),
        }
        for ps in sets
    ]
