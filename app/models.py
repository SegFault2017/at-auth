import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String, default="clerk")
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="user")
    problem_sets: Mapped[list["ProblemSet"]] = relationship(back_populates="user")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    problem_set_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("problem_sets.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String, index=True)
    mode: Mapped[str] = mapped_column(String)  # "free" | "problem_set"
    topic_tags: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submit_index: Mapped[int] = mapped_column(Integer, default=1)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    verdict: Mapped[str] = mapped_column(String)  # "accepted" | "wrong_answer" | "error"
    passed: Mapped[int] = mapped_column(Integer)
    failed: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    # {"normal"|"edge"|"stress": {"passed": int, "total": int}}
    case_categories: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 5, accepted only

    user: Mapped["User"] = relationship(back_populates="attempts")


class ProblemSet(Base):
    __tablename__ = "problem_sets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String)  # "interview_sim" | "drill"
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    problems: Mapped[list] = mapped_column(JSON, default=list)  # [{slug, time_limit_seconds}]

    user: Mapped["User"] = relationship(back_populates="problem_sets")
