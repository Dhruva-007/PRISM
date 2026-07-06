# PRISM Backend — Production Dockerfile
# Multi-stage build for minimal image size

# ── Stage 1: Install dependencies ──────────────────────────────────
FROM python:3.13-slim AS dependencies

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production runtime ────────────────────────────────────
FROM python:3.13-slim AS production

WORKDIR /app

COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

COPY app/ ./app/

ENV PORT=8080
ENV APP_ENV=production
ENV GOOGLE_CLOUD_PROJECT_ID=prism-501414
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV VERTEX_AI_MODEL_ID=gemini-2.5-flash
ENV FIREBASE_SERVICE_ACCOUNT_PATH=""
ENV ALLOWED_ORIGINS=https://prism-frontend-*.run.app,http://localhost:3000
ENV DEBUG=false

RUN useradd --create-home --shell /bin/bash prism
USER prism

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level info"]