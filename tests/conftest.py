import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.auth.backend import UserIdentity
from app.auth.dependencies import get_auth_backend
from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db):
    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class MockAuth:
    def __init__(self, provider_id: str, email: str):
        self.identity = UserIdentity(provider_id=provider_id, email=email)

    async def verify_token(self, token: str) -> UserIdentity:
        if token == "bad":
            raise ValueError("bad token")
        return self.identity


@pytest.fixture
def auth_as(client):
    """Make every token resolve to this identity, except "bad", which fails verification."""
    def _auth_as(provider_id: str = "clerk_001", email: str = "u@example.com"):
        app.dependency_overrides[get_auth_backend] = lambda: MockAuth(provider_id, email)
    return _auth_as
