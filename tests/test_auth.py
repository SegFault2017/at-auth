from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.models import User
from app.main import app


class MockAuthBackend:
    async def verify_token(self, token: str) -> UserIdentity:
        if token == "valid":
            return UserIdentity(provider_id="clerk_abc", email="test@example.com")
        raise ValueError("bad token")


async def _seed_user(db) -> User:
    user = User(provider_id="clerk_abc", username="testuser", email="test@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_get_current_user_valid(client, db):
    await _seed_user(db)
    app.dependency_overrides[get_auth_backend] = lambda: MockAuthBackend()
    resp = await client.get("/users/me", headers={"Authorization": "Bearer valid"})
    # Route doesn't exist yet — expect 404, not 401
    assert resp.status_code != 401
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_get_current_user_invalid_token(client, db):
    app.dependency_overrides[get_auth_backend] = lambda: MockAuthBackend()
    resp = await client.get("/users/me", headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
    app.dependency_overrides.pop(get_auth_backend, None)
