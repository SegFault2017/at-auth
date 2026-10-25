from datetime import datetime, timedelta, timezone
from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.models import User, Attempt
from app.main import app


class MockAuth:
    async def verify_token(self, token: str) -> UserIdentity:
        return UserIdentity(provider_id="clerk_001", email="u@example.com")


T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)


def _attempt(user, tags, verdict, submit_index=1, hints=0, minutes=5, day=0):
    started = T0 + timedelta(days=day)
    return Attempt(
        user_id=user.id, slug="p", mode="free", topic_tags=tags,
        started_at=started, submitted_at=started + timedelta(minutes=minutes),
        submit_index=submit_index, hints_used=hints, verdict=verdict,
        passed=1, failed=0, total=1,
    )


async def _setup(db):
    user = User(provider_id="clerk_001", email="u@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    db.add_all([
        # Array: clean first-try solve; a first try with hints; a retry that passed.
        _attempt(user, ["Array"], "accepted", minutes=5, day=0),
        _attempt(user, ["Array"], "accepted", hints=2, minutes=15, day=1),
        _attempt(user, ["Array"], "wrong_answer", minutes=60, day=2),
        _attempt(user, ["Array"], "accepted", submit_index=2, minutes=10, day=3),
        # Graph: only ever failed.
        _attempt(user, ["Graph"], "wrong_answer"),
        _attempt(user, ["Graph"], "error", submit_index=2),
    ])
    await db.commit()


async def test_mastery_over_new_formula(client, db):
    await _setup(db)
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.get("/users/me/mastery", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    data = resp.json()
    topics = {m["topic"]: m for m in data}

    array = topics["Array"]
    assert array["attempts_count"] == 4
    # 3 first tries: a clean accept, an accept with hints, a wrong answer. 1 is clean.
    assert array["clean_solve_rate"] == 1 / 3
    # accepted only: 5, 15, 10 minutes; hints 0, 2, 0
    assert array["avg_time_seconds"] == 600
    assert array["avg_hints"] == 2 / 3
    assert array["last_solved_at"].startswith("2026-03-04T10:10:00")

    graph = topics["Graph"]
    assert graph["attempts_count"] == 2
    assert graph["clean_solve_rate"] == 0
    assert graph["avg_time_seconds"] is None
    assert graph["avg_hints"] is None
    assert graph["last_solved_at"] is None

    assert data[0]["topic"] == "Graph"
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_mastery_empty_for_new_user(client, db):
    app.dependency_overrides[get_auth_backend] = lambda: MockAuth()
    resp = await client.get("/users/me/mastery", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    assert resp.json() == []
    app.dependency_overrides.pop(get_auth_backend, None)
