FROM python:3.11-slim

WORKDIR /app

# 4. `requirements.txt` 파일을 복사하고 필요한 Python 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 프로젝트 파일을 복사
COPY . .

# 6. `main.py` 파일 실행
CMD ["python", "main.py"]
