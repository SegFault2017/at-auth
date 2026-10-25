from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.main import app


class MockAuth:
    async def verify_token(self, token: str) -> UserIdentity:
        return UserIdentity(provider_id="clerk_001", email="u@example.com")


def override(backend):
    app.dependency_overrides[get_auth_backend] = lambda: backend


def clear():
    app.dependency_overrides.pop(get_auth_backend, None)


async def test_get_me(client, db):
    from app.models import User
    user = User(provider_id="clerk_001", email="u@example.com")
    db.add(user)
    await db.commit()
    override(MockAuth())
    resp = await client.get("/users/me", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "u@example.com"
    assert "username" not in body
    clear()
