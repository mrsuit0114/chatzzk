FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

# 1. DB 마이그레이션에 필요한 최소한의 의존성만 설치
COPY ./scripts/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 2. DB 모델과 데이터 접근 로직이 있는 packages만 복사
#    services 디렉토리는 복사하지 않음
COPY ./scripts /app/scripts
COPY ./chatzzk/packages /app/chatzzk/packages

CMD ["python", "-m", "scripts.init_db" ]
