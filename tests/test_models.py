import uuid
from app.models import User, Attempt


async def test_user_create(db):
    user = User(
        provider_id="clerk_123",
        email="alice@example.com",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    assert isinstance(user.id, uuid.UUID)
    assert user.provider == "clerk"


async def test_attempt_create(db):
    user = User(provider_id="clerk_456", email="bob@example.com")
    db.add(user)
    await db.commit()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    a = Attempt(
        user_id=user.id,
        slug="two-sum",
        mode="free",
        topic_tags=["Array", "Hash Table"],
        started_at=now,
        submitted_at=now,
        verdict="accepted",
        passed=3,
        failed=0,
        total=3,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    assert a.topic_tags == ["Array", "Hash Table"]
    assert a.hints_used == 0
    assert a.submit_index == 1
