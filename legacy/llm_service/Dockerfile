FROM python:3.11-slim

WORKDIR /app

COPY llm_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY common /app/common
RUN pip install /app/common

COPY llm_service/src/ ./src/


CMD ["python", "-u", "src/main.py"]
