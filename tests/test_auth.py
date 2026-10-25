from sqlalchemy import select
from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.models import User
from app.main import app


class MockAuthBackend:
    def __init__(self, provider_id="clerk_abc", email="test@example.com"):
        self.identity = UserIdentity(provider_id=provider_id, email=email)

    async def verify_token(self, token: str) -> UserIdentity:
        if token == "valid":
            return self.identity
        raise ValueError("bad token")


def override(backend):
    app.dependency_overrides[get_auth_backend] = lambda: backend


def clear():
    app.dependency_overrides.pop(get_auth_backend, None)


async def _users(db) -> list[User]:
    return list((await db.execute(select(User))).scalars().all())


async def test_first_request_creates_user(client, db):
    override(MockAuthBackend())
    resp = await client.get("/users/me", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"
    users = await _users(db)
    assert [(u.provider_id, u.email) for u in users] == [("clerk_abc", "test@example.com")]
    clear()


async def test_existing_user_found_by_subject(client, db):
    db.add(User(provider_id="clerk_abc", email="test@example.com"))
    await db.commit()
    override(MockAuthBackend())
    resp = await client.get("/users/me", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 200
    assert len(await _users(db)) == 1
    clear()


async def test_resignup_rekeys_by_email(client, db):
    old = User(provider_id="clerk_old", email="test@example.com")
    db.add(old)
    await db.commit()
    old_id = old.id
    override(MockAuthBackend(provider_id="clerk_new"))
    resp = await client.get("/users/me", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 200
    assert resp.json()["id"] == str(old_id)
    users = await _users(db)
    assert [(u.id, u.provider_id) for u in users] == [(old_id, "clerk_new")]
    clear()


async def test_token_without_email_returns_401(client, db):
    override(MockAuthBackend(email=""))
    resp = await client.get("/users/me", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 401
    assert await _users(db) == []
    clear()


async def test_invalid_token_returns_401(client, db):
    override(MockAuthBackend())
    resp = await client.get("/users/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
    clear()


async def test_auth_sync_removed(client):
    override(MockAuthBackend())
    resp = await client.post(
        "/auth/sync",
        json={"email": "test@example.com"},
        headers={"Authorization": "Bearer valid"},
    )
    assert resp.status_code == 404
    clear()


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
