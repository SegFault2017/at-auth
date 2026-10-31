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
| `DATABASE_URL` | `sqlite+aiosqlite:///./at_user.db` | A Postgres URL as Neon issues it works as-is (`postgresql://...?sslmode=require`). Git ignores the SQLite file. |
| `CLERK_JWKS_URL` | none | Your Clerk instance's `/.well-known/jwks.json`. |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | A JSON list of frontend origins. |

The app creates its tables on startup. There is no migration framework, so after a schema
change, delete the local SQLite file.

## Deploy (Google Cloud Run)

The database is the Neon project `algo-trainer` (`bold-rice-16010599`, AWS us-east-1).
The service runs in `us-east4` (N. Virginia), next to it. Cloud Build builds the
`Dockerfile` remotely, so local Docker is not needed. `.gcloudignore` keeps `.env` out
of the upload.

One-time setup, with `PROJECT` set to the GCP project ID:

```bash
gcloud config set project "$PROJECT"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# Runtime identity that can read only its own secret
gcloud iam service-accounts create at-auth-run
SA="at-auth-run@$PROJECT.iam.gserviceaccount.com"
grep '^DATABASE_URL=' .env | cut -d= -f2- | tr -d '"\n' |
  gcloud secrets create at-auth-database-url --data-file=-
gcloud secrets add-iam-policy-binding at-auth-database-url \
  --member="serviceAccount:$SA" --role=roles/secretmanager.secretAccessor
```

Deploy (repeat for each release):

```bash
gcloud run deploy at-auth --source . --region us-east4 \
  --service-account "$SA" --allow-unauthenticated \
  --min-instances 0 --max-instances 2 --cpu 1 --memory 512Mi \
  --set-secrets DATABASE_URL=at-auth-database-url:latest \
  --set-env-vars '^@^CLERK_JWKS_URL=https://<clerk-domain>/.well-known/jwks.json@CORS_ORIGINS=["https://<frontend-domain>"]'
```

- `--allow-unauthenticated` lets browsers reach the service. The app itself rejects
  requests without a valid Clerk token.
- `--min-instances 0` keeps the service in the free tier. Expect a cold start of a few seconds.
- `--max-instances 2` caps cost and the number of Neon connections.
- `^@^` changes the env-var separator to `@`, because the `CORS_ORIGINS` JSON list contains commas.
