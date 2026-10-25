import uuid
from app.models import Attempt

AUTH = {"Authorization": "Bearer tok"}


def _attempt(**overrides) -> dict:
    return {
        "slug": "two-sum",
        "topic_tags": ["Array", "Hash Table"],
        "started_at": "2026-02-28T10:00:00Z",
        "submitted_at": "2026-02-28T10:05:00Z",
        "submit_index": 1,
        "hints_used": 1,
        "verdict": "accepted",
        "passed": 20,
        "failed": 0,
        "total": 20,
        "runtime_ms": 142.3,
        "case_categories": {
            "normal": {"passed": 12, "total": 12},
            "edge": {"passed": 6, "total": 6},
            "stress": {"passed": 2, "total": 2},
        },
        "confidence": 4,
    } | overrides


async def test_create_attempt_persists_new_shape(client, db, auth_as):
    auth_as()
    resp = await client.post("/attempts", json=_attempt(), headers=AUTH)
    assert resp.status_code == 201

    row = await db.get(Attempt, uuid.UUID(resp.json()["id"]))
    assert row is not None
    assert row.mode == "free"
    assert row.verdict == "accepted"
    assert (row.passed, row.failed, row.total) == (20, 0, 20)
    assert row.submit_index == 1
    assert row.case_categories["edge"] == {"passed": 6, "total": 6}
    assert row.confidence == 4
    assert abs(row.runtime_ms - 142.3) < 0.01


async def test_attempt_in_problem_set_gets_problem_set_mode(client, db, auth_as):
    auth_as()
    ps = await client.post("/problemsets", json={"mode": "drill", "problems": []}, headers=AUTH)
    resp = await client.post(
        "/attempts", json=_attempt(problem_set_id=ps.json()["id"]), headers=AUTH
    )
    assert resp.status_code == 201
    row = await db.get(Attempt, uuid.UUID(resp.json()["id"]))
    assert row.mode == "problem_set"
    assert str(row.problem_set_id) == ps.json()["id"]


async def test_failed_attempt_recorded_without_confidence(client, db, auth_as):
    auth_as()
    resp = await client.post(
        "/attempts",
        json=_attempt(verdict="wrong_answer", passed=18, failed=2, submit_index=2,
                      confidence=None),
        headers=AUTH,
    )
    assert resp.status_code == 201
    row = await db.get(Attempt, uuid.UUID(resp.json()["id"]))
    assert row.verdict == "wrong_answer"
    assert row.confidence is None


async def test_confidence_rejected_unless_accepted(client, auth_as):
    auth_as()
    resp = await client.post(
        "/attempts", json=_attempt(verdict="error", confidence=3), headers=AUTH
    )
    assert resp.status_code == 422


async def test_create_attempt_requires_auth(client):
    resp = await client.post("/attempts", json=_attempt())
    assert resp.status_code in (401, 403)


async def test_sessions_route_removed(client, auth_as):
    auth_as()
    resp = await client.post("/sessions", json=_attempt(), headers=AUTH)
    assert resp.status_code == 404


async def test_list_my_attempts(client, auth_as):
    auth_as()
    await client.post("/attempts", json=_attempt(), headers=AUTH)
    resp = await client.get("/users/me/attempts", headers=AUTH)
    assert resp.status_code == 200
    [a] = resp.json()
    assert a["slug"] == "two-sum"
    assert a["mode"] == "free"
    assert a["verdict"] == "accepted"
    assert a["submit_index"] == 1
    assert a["case_categories"]["stress"] == {"passed": 2, "total": 2}
