FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv python install 3.11 \
    && uv venv --python 3.11 \
    && uv sync --extra asr-server

COPY chatzzk/services/asr_inference_server2 /app/chatzzk/services/asr_inference_server
COPY chatzzk/packages /app/chatzzk/packages

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "chatzzk.services.asr_inference_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
