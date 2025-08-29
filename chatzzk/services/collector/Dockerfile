FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

# 1. 버전이 고정된 requirements.txt만 복사
COPY ./chatzzk/services/collector/requirements.txt /app/requirements.txt

# 2. pip으로 설치
RUN pip install --no-cache-dir -r /app/requirements.txt

# 3. 소스 코드 복사
COPY ./chatzzk /app/chatzzk
COPY ./scripts /app/scripts

CMD ["tail", "-f", "/dev/null"]
