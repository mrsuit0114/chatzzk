FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV WHISPERX_MODEL_DIR=/app/whisperx_models

COPY src/ ./src/

CMD ["python", "-u", "src/main.py"]
