from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.backend import AuthBackend
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
    if not identity.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has no email claim")

    by_subject = select(User).where(User.provider_id == identity.provider_id)
    user = (await db.execute(by_subject)).scalar_one_or_none()
    if user:
        return user

    # Clerk gives a re-signup under the same email a new subject, so re-key the old row.
    user = (await db.execute(select(User).where(User.email == identity.email))).scalar_one_or_none()
    if user:
        user.provider_id = identity.provider_id
    else:
        user = User(provider_id=identity.provider_id, provider="clerk", email=identity.email)
        db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # A concurrent first request provisioned the same learner; use its row.
        await db.rollback()
        user = (await db.execute(by_subject)).scalar_one_or_none()
        if not user:
            raise
    return user
