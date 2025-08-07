FROM python:3.11-slim

# 필요한 패키지 리스트를 업데이트하고 ffmpeg를 설치합니다.
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "-u", "src/main.py"]
