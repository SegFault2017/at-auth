# at-auth

at-auth stores learner identity and Attempts for Algo Trainer. `CONTEXT.md` defines the domain language.

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8002   # the executor uses 8001
.venv/bin/python -m pytest -v
```

## Configuration

The app reads these settings from the environment or from `.env`. `.env.example` has a template.

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./at_user.db` | For Postgres, use `postgresql+asyncpg://...`. Git ignores the SQLite file. |
| `CLERK_JWKS_URL` | none | Your Clerk instance's `/.well-known/jwks.json`. |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | A JSON list of frontend origins. |

The app creates its tables on startup. There is no migration framework, so after a schema
change, delete the local SQLite file.
