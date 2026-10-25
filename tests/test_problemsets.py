import uuid
from app.models import User, ProblemSet


async def _seed(db) -> User:
    user = User(provider_id="clerk_001", email="u@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_create_and_fetch_problem_set(client, db, auth_as):
    await _seed(db)
    auth_as()

    resp = await client.post(
        "/problemsets",
        json={
            "mode": "drill",
            "problems": [{"slug": "two-sum", "time_limit_seconds": 1800}],
        },
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 201
    assert "status" not in resp.json()
    ps_id = resp.json()["id"]

    resp2 = await client.get(f"/problemsets/{ps_id}", headers={"Authorization": "Bearer tok"})
    assert resp2.status_code == 200
    assert resp2.json()["problems"][0]["slug"] == "two-sum"


async def test_create_problem_set_ignores_body_user_id(client, db, auth_as):
    user = await _seed(db)
    other = User(provider_id="clerk_999", email="other@example.com")
    db.add(other)
    await db.commit()
    auth_as()

    resp = await client.post(
        "/problemsets",
        json={"user_id": str(other.id), "mode": "drill", "problems": []},
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 201
    ps = await db.get(ProblemSet, uuid.UUID(resp.json()["id"]))
    assert ps.user_id == user.id


async def test_get_problem_set_not_found(client, db, auth_as):
    await _seed(db)
    auth_as()
    resp = await client.get(
        "/problemsets/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 404
