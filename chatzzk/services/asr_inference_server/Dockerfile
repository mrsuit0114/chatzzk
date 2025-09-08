FROM 12.2.2-cudnn8-3.11

WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app"
COPY ./models /models

COPY ./chatzzk/services/asr_inference_server/requirements.txt /app/requirements.txt

RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

COPY ./chatzzk /app/chatzzk

EXPOSE 8000

CMD ["uvicorn", "chatzzk.services.asr_inference_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
