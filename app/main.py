from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import create_tables
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.sessions import router as sessions_router
from app.routes.problemsets import router as problemsets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(problemsets_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
