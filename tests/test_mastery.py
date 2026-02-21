from datetime import datetime, timezone
from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.models import User, Session
from app.main import app


class MockAuth:
    async def verify_token(self, token: str) -> UserIdentity:
        return UserIdentity(provider_id="clerk_001", email="u@example.com")


async def _setup(db):
    user = User(provider_id="clerk_001", username="alice", email="u@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    now = datetime.now(timezone.utc)
    sessions = [
        Session(user_id=user.id, slug="two-sum", mode="free",
                topic_tags=["Array", "Hash Table"],
                started_at=now, completed_at=now,
                time_taken_seconds=300, hints_used=0, attempts=1),
        Session(user_id=user.id, slug="climbing-stairs", mode="free",
                topic_tags=["Dynamic Programming"],
                started_at=now, completed_at=now,
                time_taken_seconds=900, hints_used=3, attempts=2),
        Session(user_id=user.id, slug="contains-duplicate", mode="free",
                topic_tags=["Array"],
                started_at=now, completed_at=now,
                time_taken_seconds=240, hints_used=1, attempts=1),
    ]
    for s in sessions:
        db.add(s)
    await db.commit()
    return user


async def test_mastery_aggregates_by_topic(client, db):
    await _setup(db)
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.get("/users/me/mastery", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    data = resp.json()
    topics = {m["topic"]: m for m in data}
    assert "Array" in topics
    assert "Dynamic Programming" in topics
    assert topics["Array"]["sessions_count"] == 2
    # DP: 0 clean solves → lowest clean_solve_rate → first in sorted list
    assert data[0]["topic"] == "Dynamic Programming"
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_mastery_empty_for_new_user(client, db):
    user = User(provider_id="clerk_001", username="alice", email="u@example.com")
    db.add(user)
    await db.commit()
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.get("/users/me/mastery", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    assert resp.json() == []
    app.dependency_overrides.pop(get_auth_backend, None)
