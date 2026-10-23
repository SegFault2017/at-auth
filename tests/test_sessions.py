import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.models import User, Session
from app.main import app


class MockAuth:
    async def verify_token(self, token: str) -> UserIdentity:
        return UserIdentity(provider_id="clerk_001", email="u@example.com")


async def _seed(db) -> User:
    user = User(provider_id="clerk_001", username="alice", email="u@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_session(client, db):
    await _seed(db)
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.post(
        "/sessions",
        json={
            "slug": "two-sum",
            "topic_tags": ["Array", "Hash Table"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "time_taken_seconds": 540,
            "hints_used": 1,
            "hint_level_reached": 2,
            "passed_core_tests": True,
            "passed_edge_tests": False,
            "confidence": 4,
        },
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 201
    assert "id" in resp.json()
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_create_session_requires_auth(client):
    resp = await client.post(
        "/sessions",
        json={"slug": "two-sum", "started_at": "2026-01-01T00:00:00Z"},
    )
    assert resp.status_code in (401, 403)


async def test_create_session_persists_execution_fields(client, db):
    await _seed(db)
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.post("/sessions", json={
        "slug": "two-sum",
        "topic_tags": ["array"],
        "mode": "free",
        "started_at": "2026-02-28T10:00:00Z",
        "completed_at": "2026-02-28T10:05:00Z",
        "time_taken_seconds": 300,
        "hints_used": 1,
        "hint_level_reached": 1,
        "attempts": 1,
        "passed_core_tests": True,
        "confidence": 4,
        "hidden_tests_passed": 18,
        "hidden_tests_failed": 2,
        "hidden_tests_total": 20,
        "runtime_ms": 142.3,
    }, headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    # Verify execution fields were persisted to the database
    row = await db.get(Session, uuid.UUID(session_id))
    assert row is not None
    assert row.hidden_tests_passed == 18
    assert row.hidden_tests_failed == 2
    assert row.hidden_tests_total == 20
    assert abs(row.runtime_ms - 142.3) < 0.01

    app.dependency_overrides.pop(get_auth_backend, None)
