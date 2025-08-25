FROM python:3.11-slim

WORKDIR /app

# 1. 의존성 파일 먼저 복사 (Docker 레이어 캐시 최적화)
COPY ./packages/requirements.txt /app/packages/requirements.txt
COPY ./services/collector/requirements.txt /app/services/collector/requirements.txt

# 2. 공유 패키지 및 서비스별 의존성 설치
RUN pip install --no-cache-dir -r /app/packages/requirements.txt \
    && pip install --no-cache-dir -r /app/services/collector/requirements.txt

# 3. 실제 소스 코드 복사
# 'chatzzk' 디렉토리 전체를 복사하여 절대 경로 임포트가 가능하게 함
COPY ./chatzzk /app/chatzzk

# 4. PYTHONPATH 설정 (필수!)
# 컨테이너 내에서 `from chatzzk.packages import ...`가 동작하도록 함
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 5. 서비스 실행
CMD ["python", "-m", "chatzzk.services.collector.main"]
