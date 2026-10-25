import uuid
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Attempt

router = APIRouter(tags=["attempts"])


class CategoryCount(BaseModel):
    passed: int
    total: int


class AttemptCreate(BaseModel):
    slug: str
    topic_tags: list[str] = []
    problem_set_id: uuid.UUID | None = None
    started_at: datetime
    submitted_at: datetime
    submit_index: int = Field(1, ge=1)
    hints_used: int = 0
    verdict: Literal["accepted", "wrong_answer", "error"]
    passed: int
    failed: int
    total: int
    runtime_ms: float | None = None
    case_categories: dict[Literal["normal", "edge", "stress"], CategoryCount] = {}
    confidence: int | None = Field(None, ge=1, le=5)

    @model_validator(mode="after")
    def confidence_only_when_accepted(self):
        if self.confidence is not None and self.verdict != "accepted":
            raise ValueError("only an accepted Attempt can have a confidence")
        return self


class AttemptOut(AttemptCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: Literal["free", "problem_set"]


@router.post("/attempts", status_code=201)
async def create_attempt(
    body: AttemptCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attempt = Attempt(
        user_id=user.id,
        mode="problem_set" if body.problem_set_id else "free",
        **body.model_dump(),
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return {"id": str(attempt.id)}


@router.get("/users/me/attempts", response_model=list[AttemptOut])
async def get_my_attempts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Attempt)
        .where(Attempt.user_id == user.id)
        .order_by(Attempt.submitted_at.desc())
    )
    return result.scalars().all()
