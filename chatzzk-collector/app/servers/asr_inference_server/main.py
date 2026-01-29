import asyncio
import time
from contextlib import asynccontextmanager
from typing import Annotated

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from loguru import logger

from app.servers.asr_inference_server.settings import InferenceServerSettings
from chatzzk_clients.ml.asr import create_asr_client
from chatzzk_core.schemas.internal import ASRResponse

settings = InferenceServerSettings()
TARGET_SAMPLE_RATE = settings.target_sample_rate
MAX_SPEECH_DURATION_S = settings.max_speech_duration_s
MAX_SAMPLES = TARGET_SAMPLE_RATE * MAX_SPEECH_DURATION_S
WORKER_NUM = settings.worker_num


class ASRPool:
    def __init__(self, clients: list):
        self.clients = clients
        self._queue = asyncio.Queue()

        for client in clients:
            self._queue.put_nowait(client)

    async def acquire(self):
        return await self._queue.get()

    async def release(self, client):
        await self._queue.put(client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ASR Inference Server is starting up...")
    try:
        clients = [create_asr_client(settings.asr_model_config) for _ in range(WORKER_NUM)]
        app.state.asr_pool = ASRPool(clients)
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
    pool = app.state.asr_pool
    asr_client = await pool.acquire()

    try:
        # 1. 수신된 바이트를 NumPy 배열로 변환
        byte_data = await audio_bytes.read()
        audio_chunk_np = np.frombuffer(byte_data, dtype=np.dtype(dtype))

        current_samples = len(audio_chunk_np)

        if current_samples > MAX_SAMPLES:
            logger.warning(
                f"⚠️ Audio chunk exceeds limit ({current_samples} samples). "
                f"Truncating to {MAX_SPEECH_DURATION_S}s ({MAX_SAMPLES} samples)."
            )
            audio_chunk_np = audio_chunk_np[:MAX_SAMPLES]

        # 2. ASR 클라이언트를 사용하여 추론
        inference_start = time.time()
        transcription_text = await asr_client.transcribe(audio_chunk_np)
        inference_time = time.time() - inference_start
        logger.info(
            f"Transcription successful. Text: {transcription_text}, [ASR] model_id={id(asr_client)}, inference time: {inference_time}"
        )
        return ASRResponse(text=transcription_text)

    finally:
        await pool.release(asr_client)


@app.get("/health")
def health_check():
    pool = getattr(app.state, "asr_pool", None)
    is_ready = pool is not None and len(pool.clients) > 0
    return {
        "status": "ok" if is_ready else "loading",
        "models_loaded": len(pool.clients) if pool else 0,
    }
