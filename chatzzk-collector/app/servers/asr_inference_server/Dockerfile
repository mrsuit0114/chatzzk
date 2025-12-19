FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

COPY app/ app/
COPY packages/ packages/

# 8. Python 환경 구성 및 의존성 설치
# (1) uv python install 3.11: Ubuntu 22.04 기본은 3.10이므로, uv로 3.11을 관리형으로 설치합니다.
# (2) uv sync:
#     --frozen: lock 파일 준수
#     --no-dev: 개발 툴 제외
#     --package: 해당 서비스만 설치
#     --extra whisperx: GPU 이미지이므로 whisperx 기능을 활성화 (필요시 제거)
RUN uv python install 3.11 && \
    uv sync --frozen --no-dev --package asr-inference-server --extra whisperx

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.servers.asr_inference_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
