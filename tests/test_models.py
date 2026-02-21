import uuid
from app.models import User, Session, ProblemSet


async def test_user_create(db):
    user = User(
        provider_id="clerk_123",
        username="alice",
        email="alice@example.com",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    assert isinstance(user.id, uuid.UUID)
    assert user.provider == "clerk"


async def test_session_create(db):
    user = User(provider_id="clerk_456", username="bob", email="bob@example.com")
    db.add(user)
    await db.commit()

    from datetime import datetime, timezone
    s = Session(
        user_id=user.id,
        slug="two-sum",
        mode="free",
        topic_tags=["Array", "Hash Table"],
        started_at=datetime.now(timezone.utc),
        time_taken_seconds=600,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    assert s.topic_tags == ["Array", "Hash Table"]
    assert s.hints_used == 0
