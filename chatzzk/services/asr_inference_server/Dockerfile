# FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# ENV DEBIAN_FRONTEND=noninteractive
# ENV TZ=Asia/Seoul

# # Install necessary system packages and Python
# RUN apt-get update && apt-get install -y \
# tzdata software-properties-common curl wget git \
# && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
# && echo $TZ > /etc/timezone \
# && add-apt-repository ppa:deadsnakes/ppa -y \
# && apt-get update \
# && apt-get install -y \
# python3.11 \
# python3.11-dev \
# python3.11-distutils \
# python3-pip \
# && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
# && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
# && python --version && python3 --version \
# && rm -rf /var/lib/apt/lists/*


FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04-python3.11
WORKDIR /app

# Copy requirements file first to take advantage of Docker caching
COPY services/asr_inference_server/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY services/asr_inference_server /app/chatzzk/services/asr_inference_server
COPY packages /app/chatzzk/packages

EXPOSE 8000

CMD ["uvicorn", "chatzzk.services.asr_inference_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
