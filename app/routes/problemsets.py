import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, ProblemSet

router = APIRouter(prefix="/problemsets", tags=["problemsets"])


class ProblemSetCreate(BaseModel):
    mode: str  # "interview_sim" | "drill"
    problems: list[dict]  # [{slug, time_limit_seconds}]


class ProblemSetOut(ProblemSetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    generated_at: datetime


@router.post("", status_code=201, response_model=ProblemSetOut)
async def create_problem_set(
    body: ProblemSetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ps = ProblemSet(user_id=user.id, **body.model_dump())
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return ps


@router.get("/{problem_set_id}", response_model=ProblemSetOut)
async def get_problem_set(
    problem_set_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProblemSet).where(
            ProblemSet.id == problem_set_id,
            ProblemSet.user_id == user.id,
        )
    )
    ps = result.scalar_one_or_none()
    if not ps:
        raise HTTPException(status_code=404, detail="Problem set not found")
    return ps


@router.get("", response_model=list[ProblemSetOut])
async def list_problem_sets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProblemSet)
        .where(ProblemSet.user_id == user.id)
        .order_by(ProblemSet.generated_at.desc())
    )
    return result.scalars().all()
