FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

COPY app/ app/
COPY packages/ packages/

RUN uv python install 3.11 && \
    uv sync --frozen --no-dev --extra pipeline

ENV PATH="/app/.venv/bin:$PATH"
