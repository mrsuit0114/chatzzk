# services/collector/Dockerfile 예시
FROM python:3.9

# 프로젝트 루트를 /app 으로 복사
WORKDIR /app
COPY . .

# PYTHONPATH 환경변수 설정
# 이를 통해 /app (프로젝트 루트)에서도 모듈을 찾을 수 있게 됨
ENV PYTHONPATH "${PYTHONPATH}:/app"

# collector 서비스의 의존성 설치
RUN pip install -r services/collector/requirements.txt

# collector 실행 명령어
CMD ["celery", "-A", "services.collector.tasks.celery_app", "worker", "-l", "info"]
