FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

RUN apt-get update && apt-get install -y ffmpeg curl

WORKDIR /app

COPY vod_context/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# common 라이브러리를 프로젝트 루트에서 복사합니다.
COPY common /app/common
RUN pip install /app/common

# vod_context의 소스 코드를 복사합니다.
COPY vod_context/src/ ./src/

CMD ["python", "-u", "src/main.py"]
