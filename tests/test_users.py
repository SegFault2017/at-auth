from app.models import User


async def test_get_me(client, db, auth_as):
    user = User(provider_id="clerk_001", email="u@example.com")
    db.add(user)
    await db.commit()
    auth_as()
    resp = await client.get("/users/me", headers={"Authorization": "Bearer tok"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(user.id)
    assert body["email"] == "u@example.com"
    assert "username" not in body
