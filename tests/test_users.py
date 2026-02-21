from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.main import app


class MockAuth:
    async def verify_token(self, token: str) -> UserIdentity:
        return UserIdentity(provider_id="clerk_001", email="u@example.com")


class MockAuthBad:
    async def verify_token(self, token: str) -> UserIdentity:
        raise ValueError("bad")


def override(backend):
    app.dependency_overrides[get_auth_backend] = lambda: backend


def clear():
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_sync_creates_user(client):
    override(MockAuth())
    resp = await client.post(
        "/auth/sync",
        json={"username": "alice", "email": "u@example.com", "first_name": "Alice"},
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    clear()


async def test_sync_duplicate_username_returns_409(client):
    override(MockAuth())
    await client.post(
        "/auth/sync",
        json={"username": "alice", "email": "u@example.com"},
        headers={"Authorization": "Bearer tok"},
    )
    class MockAuth2:
        async def verify_token(self, token: str) -> UserIdentity:
            return UserIdentity(provider_id="clerk_002", email="other@example.com")
    override(MockAuth2())
    resp = await client.post(
        "/auth/sync",
        json={"username": "alice", "email": "other@example.com"},
        headers={"Authorization": "Bearer tok"},
    )
    assert resp.status_code == 409
    clear()


async def test_sync_bad_token_returns_401(client):
    override(MockAuthBad())
    resp = await client.post(
        "/auth/sync",
        json={"username": "x", "email": "x@x.com"},
        headers={"Authorization": "Bearer bad"},
    )
    assert resp.status_code == 401
    clear()


async def test_get_me(client, db):
    from app.models import User
    user = User(provider_id="clerk_001", username="alice", email="u@example.com")
    db.add(user)
    await db.commit()
    override(MockAuth())
    resp = await client.get("/users/me", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    clear()
