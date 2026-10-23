import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String, default="clerk")
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    problem_sets: Mapped[list["ProblemSet"]] = relationship(back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    problem_set_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("problem_sets.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String, index=True)
    mode: Mapped[str] = mapped_column(String)  # "free" | "problem_set"
    topic_tags: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    hint_level_reached: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    passed_core_tests: Mapped[bool] = mapped_column(Boolean, default=False)
    passed_edge_tests: Mapped[bool] = mapped_column(Boolean, default=False)
    solution_time_complexity: Mapped[str | None] = mapped_column(String, nullable=True)
    solution_space_complexity: Mapped[str | None] = mapped_column(String, nullable=True)
    is_optimal: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5
    hidden_tests_passed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hidden_tests_failed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hidden_tests_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class ProblemSet(Base):
    __tablename__ = "problem_sets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String)  # "interview_sim" | "drill"
    status: Mapped[str] = mapped_column(String, default="active")  # "active" | "completed"
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    problems: Mapped[list] = mapped_column(JSON, default=list)  # [{slug, time_limit_seconds}]

    user: Mapped["User"] = relationship(back_populates="problem_sets")
