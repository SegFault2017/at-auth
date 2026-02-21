from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.auth.backend import AuthBackend
from app.auth.dependencies import bearer, get_auth_backend
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class SyncRequest(BaseModel):
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None


@router.post("/sync")
async def sync_user(
    body: SyncRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
    auth: AuthBackend = Depends(get_auth_backend),
):
    try:
        identity = await auth.verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.provider_id == identity.provider_id))
    user = result.scalar_one_or_none()

    if not user:
        existing = await db.execute(select(User).where(User.username == body.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")
        user = User(
            provider_id=identity.provider_id,
            provider="clerk",
            username=body.username,
            email=body.email,
            first_name=body.first_name,
            last_name=body.last_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
