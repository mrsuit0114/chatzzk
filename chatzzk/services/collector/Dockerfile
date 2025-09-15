FROM python:3.11-slim

# 시스템 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 파이썬 의존성 설치
COPY chatzzk/services/collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY chatzzk /app/chatzzk

# 진입점 스크립트 복사 및 실행 권한 부여
COPY chatzzk/services/collector/docker/*.sh /docker/
RUN chmod +x /docker/*.sh

# 기본 진입점은 Celery 워커용 스크립트로 설정
ENTRYPOINT ["/docker/worker_entrypoint.sh"]
