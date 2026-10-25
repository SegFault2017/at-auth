from sqlalchemy import select
from app.models import User

AUTH = {"Authorization": "Bearer tok"}


async def _users(db) -> list[User]:
    return list((await db.execute(select(User))).scalars().all())


async def test_first_request_creates_user(client, db, auth_as):
    auth_as()
    resp = await client.get("/users/me", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["email"] == "u@example.com"
    users = await _users(db)
    assert [(u.provider_id, u.email) for u in users] == [("clerk_001", "u@example.com")]


async def test_existing_user_found_by_subject(client, db, auth_as):
    db.add(User(provider_id="clerk_001", email="u@example.com"))
    await db.commit()
    auth_as()
    resp = await client.get("/users/me", headers=AUTH)
    assert resp.status_code == 200
    assert len(await _users(db)) == 1


async def test_resignup_rekeys_by_email(client, db, auth_as):
    old = User(provider_id="clerk_old", email="u@example.com")
    db.add(old)
    await db.commit()
    old_id = old.id
    auth_as(provider_id="clerk_new")
    resp = await client.get("/users/me", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(old_id)
    users = await _users(db)
    assert [(u.id, u.provider_id) for u in users] == [(old_id, "clerk_new")]


async def test_token_without_email_returns_401(client, db, auth_as):
    auth_as(email="")
    resp = await client.get("/users/me", headers=AUTH)
    assert resp.status_code == 401
    assert await _users(db) == []


async def test_invalid_token_returns_401(client, auth_as):
    auth_as()
    resp = await client.get("/users/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401


async def test_auth_sync_removed(client, auth_as):
    auth_as()
    resp = await client.post("/auth/sync", json={"email": "u@example.com"}, headers=AUTH)
    assert resp.status_code == 404


async def test_cors_allows_frontend_origin(client):
    resp = await client.options(
        "/users/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"
