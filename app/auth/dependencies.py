from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.backend import AuthBackend, UserIdentity
from app.auth.clerk import ClerkAuthBackend
from app.config import get_settings
from app.database import get_db
from app.models import User

bearer = HTTPBearer()


def get_auth_backend() -> AuthBackend:
    return ClerkAuthBackend(get_settings().clerk_jwks_url)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
    auth: AuthBackend = Depends(get_auth_backend),
) -> User:
    try:
        identity = await auth.verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.provider_id == identity.provider_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
