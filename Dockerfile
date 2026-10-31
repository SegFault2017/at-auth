FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# No root at runtime; the app writes nothing to disk when DATABASE_URL points at Postgres
RUN useradd --system --uid 10001 app
USER app

# Cloud Run injects PORT (8080 by default); --proxy-headers trusts its front-end proxy
CMD exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --proxy-headers --forwarded-allow-ips='*'
