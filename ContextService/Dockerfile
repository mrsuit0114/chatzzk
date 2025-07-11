# ContextService/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# .env.example을 .env로 복사 (개발/테스트용)
COPY .env.example .env

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app 디렉토리의 모든 내용을 /app으로 복사
COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
