import time
from contextlib import asynccontextmanager
from typing import Annotated

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from loguru import logger

from app.servers.asr_inference_server.settings import InferenceServerSettings
from chatzzk_clients.ml.asr import ASRClientInterface, create_asr_client
from chatzzk_core.schemas.external import ASRResponse

asr_client: ASRClientInterface = None
settings = InferenceServerSettings()
TARGET_SAMPLE_RATE = settings.target_sample_rate
MAX_SPEECH_DURATION_S = settings.max_speech_duration_s


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asr_client
    logger.info("🚀 ASR Inference Server is starting up...")
    try:
        asr_client = create_asr_client(settings.asr_model_config)
        logger.success("✅ ASR model initialized successfully.")
    except Exception as e:
        logger.opt(exception=True).critical(f"❌ Failed to initialize ASR model: {e}")
        raise e

    # 이 부분에서 애플리케이션이 실행됩니다.
    yield

    logger.info("👋 ASR Inference Server is shutting down...")


app = FastAPI(title="ASR Inference Server", lifespan=lifespan)


# --- VOD 및 실시간 처리를 위한 공용 엔드포인트 ---
@app.post("/transcribe", response_model=ASRResponse)
async def transcribe_chunk(
    audio_bytes: Annotated[UploadFile, File(description="오디오 청크 바이너리 데이터 (float32 format normalized)")],
    dtype: Annotated[str, Form(description="NumPy 데이터 타입")] = "float32",
):
    """
    단일 오디오 청크(NumPy 배열)를 받아 ASR 추론을 수행하고,
    인식된 텍스트를 반환합니다.
    """
    if not asr_client:
        raise HTTPException(status_code=503, detail="Server is not ready, ASR model not initialized.")

    try:
        # 1. 수신된 바이트를 NumPy 배열로 변환
        byte_data = await audio_bytes.read()
        audio_chunk_np = np.frombuffer(byte_data, dtype=np.dtype(dtype))

        # 입력 오디오의 길이를 검증 (예: 최대 30초)
        if len(audio_chunk_np) > TARGET_SAMPLE_RATE * MAX_SPEECH_DURATION_S:
            raise HTTPException(
                status_code=413, detail=f"Audio chunk exceeds max duration of {MAX_SPEECH_DURATION_S}s."
            )

        # 2. ASR 클라이언트를 사용하여 추론
        inference_start = time.time()
        transcription_text = await asr_client.transcribe(audio_chunk_np)
        inference_time = time.time() - inference_start
        logger.info(
            f"Transcription successful. Text length: {len(transcription_text)}, inference time: {inference_time}"
        )
        return ASRResponse(text=transcription_text)

    except Exception as e:
        logger.opt(exception=True).error(f"Error during transcription: {e}")
        raise e


@app.get("/health")
def health_check():
    """서버 상태 및 모델 로드 여부 확인."""
    is_ready = asr_client is not None
    return {"status": "ok" if is_ready else "loading", "models_loaded": is_ready}
