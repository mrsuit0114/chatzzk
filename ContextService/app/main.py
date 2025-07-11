import asyncio
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from redis.exceptions import ConnectionError

from .redis_manager import RedisManager  # redis_manager 모듈 임포트

# .env 파일 로드
load_dotenv()

# 환경 변수 로드
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
MONITOR_REQUEST_STREAM = os.getenv("MONITOR_REQUEST_STREAM", "monitor_requests")
# AIAnalysisService의 URL, ContextService가 컨텍스트를 보낼 대상
CONTEXT_RECEIVE_URL = os.getenv("CONTEXT_RECEIVE_URL", "http://localhost:8001/context/receive")

app = FastAPI(title="ContextService")

# RedisManager 인스턴스
redis_manager: RedisManager = None

# 임시 인메모리 저장소: 실제 서비스에서는 Redis Hash, DB 등으로 대체되어야 함
# { "broadcaster_id": [{"timestamp": ..., "data": ...}, ...] }
# 현재는 ContextService가 ContextManager 역할도 겸하고 있으므로 임시로 여기에 저장합니다.
# AIAnalysisService가 직접 ContextService의 /context/retrieve 엔드포인트를 호출하는 방식으로 변경 예정
# 혹은 ContextService가 AIAnalysisService로 주기적으로 Push하는 방식으로 구현 가능
buffered_contexts: Dict[str, List[Dict[str, Any]]] = {}

# 주기적인 컨텍스트 전송 설정 (현재 AiAnalysisService로 Push하는 방식)
CONTEXT_SEND_INTERVAL_SECONDS = 5  # 5초마다 컨텍스트 전송 시도

# 주기적인 모니터링 상태 확인 및 재할당 설정
REALLOCATION_CHECK_INTERVAL_SECONDS = 30  # 30초마다 재할당 필요한지 체크
LAST_CONTEXT_RECEIVED_TIME: Dict[str, float] = {}  # 마지막으로 컨텍스트를 받은 시간 기록


# Pydantic 모델 정의
class BroadcasterStatusChange(BaseModel):
    broadcaster_id: str
    status: str  # "OPEN" or "CLOSE"
    chat_channel_id: Optional[str] = None  # 라이브 시작 시에만 존재
    timestamp: float


class WorkerContextData(BaseModel):
    broadcaster_id: str
    # 실제 워커가 보내는 컨텍스트 데이터 구조에 맞게 확장 필요
    data: Dict[str, Any]
    timestamp: float


# --- 생명주기 이벤트 ---
@app.on_event("startup")
async def startup_event():
    print("ContextService: Starting up...")
    global redis_manager
    redis_manager = RedisManager(REDIS_HOST, REDIS_PORT, REDIS_DB, MONITOR_REQUEST_STREAM)
    try:
        await redis_manager.connect()
    except ConnectionError:
        print("ContextService: Redis connection failed at startup. Exiting.")
        # Redis 연결이 없으면 서비스 동작 불가하므로 강제 종료
        os._exit(1)  # uvicorn이 종료되도록 프로세스 종료

    # 주기적인 컨텍스트 전송 태스크 시작
    asyncio.create_task(send_contexts_to_ai_analysis_periodically())
    # 주기적인 모니터링 상태 확인 및 재할당 태스크 시작
    asyncio.create_task(check_and_reallocate_monitors_periodically())


@app.on_event("shutdown")
async def shutdown_event():
    print("ContextService: Shutting down...")
    if redis_manager:
        await redis_manager.disconnect()


# --- API 엔드포인트 ---
@app.post("/broadcaster/status_change")
async def handle_broadcaster_status_change(status_data: BroadcasterStatusChange):
    """
    BroadcasterStatusWatcher로부터 방송 상태 변경 알림을 수신합니다.
    """
    broadcaster_id = status_data.broadcaster_id
    status = status_data.status
    chat_channel_id = status_data.chat_channel_id

    print(f"ContextService: Received status change for {broadcaster_id}: {status}")

    try:
        if status == "OPEN":
            # 1. Redis Set에 추가 시도 (중복 방지)
            added = await redis_manager.add_active_monitor(broadcaster_id)
            if not added:
                print(f"ContextService: Broadcaster {broadcaster_id} is already in active monitors. No action needed.")
                return {"message": f"Broadcaster {broadcaster_id} is already being monitored."}

            # 2. MonitorWorker에게 모니터링 시작 지시 발행
            await redis_manager.publish_monitor_command(
                "start_monitor",
                broadcaster_id,
                chat_channel_id=chat_channel_id,  # 치지직 채팅 채널 ID 전달
            )
            # 버퍼 초기화 (새로운 방송 시작이므로)
            buffered_contexts[broadcaster_id] = []
            LAST_CONTEXT_RECEIVED_TIME[broadcaster_id] = time.time()  # 시작 시간 기록
            print(f"ContextService: Published START command for {broadcaster_id}.")
            return {"message": f"Published START command for {broadcaster_id} to Redis Stream."}

        elif status == "CLOSE":
            # 1. Redis Set에서 제거 시도
            removed = await redis_manager.remove_active_monitor(broadcaster_id)
            if not removed:
                print(f"ContextService: Broadcaster {broadcaster_id} was not in active monitors. No action needed.")
                raise HTTPException(
                    status_code=404, detail=f"Broadcaster {broadcaster_id} not found in active monitors."
                )

            # 2. MonitorWorker에게 모니터링 중지 지시 발행
            await redis_manager.publish_monitor_command("stop_monitor", broadcaster_id)
            # 버퍼 정리 (방송 종료이므로)
            if broadcaster_id in buffered_contexts:
                del buffered_contexts[broadcaster_id]
            if broadcaster_id in LAST_CONTEXT_RECEIVED_TIME:
                del LAST_CONTEXT_RECEIVED_TIME[broadcaster_id]
            print(f"ContextService: Published STOP command for {broadcaster_id}.")
            return {"message": f"Published STOP command for {broadcaster_id} to Redis Stream."}

        else:
            raise HTTPException(status_code=400, detail="Invalid status provided. Must be 'OPEN' or 'CLOSE'.")

    except ConnectionError as e:
        raise HTTPException(status_code=500, detail=f"Redis connection error: {e}")
    except Exception as e:
        print(f"ContextService: Error handling status change for {broadcaster_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process status change: {e}")


@app.post("/context/from_worker")
async def receive_context_from_worker(context_data: WorkerContextData):
    """
    MonitorWorker로부터 컨텍스트 데이터를 수신하고 임시 저장합니다.
    """
    broadcaster_id = context_data.broadcaster_id
    data = context_data.data
    timestamp = context_data.timestamp

    # 임시 버퍼에 저장 (실제로는 Redis List, Redis Stream, DB 등에 저장)
    if broadcaster_id not in buffered_contexts:
        buffered_contexts[broadcaster_id] = []

    buffered_contexts[broadcaster_id].append({"timestamp": timestamp, "data": data})
    LAST_CONTEXT_RECEIVED_TIME[broadcaster_id] = time.time()  # 마지막 수신 시간 업데이트

    # print(f"ContextService: Received context for {broadcaster_id}. Buffer size: {len(buffered_contexts[broadcaster_id])}")
    return {"message": "Context received and buffered."}


@app.get("/context/retrieve/{broadcaster_id}")
async def retrieve_context(broadcaster_id: str, limit: int = 100):
    """
    지정된 방송인의 최신 컨텍스트 데이터를 조회합니다. (AIAnalysisService에서 풀링 시 사용)
    """
    if broadcaster_id not in buffered_contexts:
        raise HTTPException(status_code=404, detail=f"No context found for broadcaster {broadcaster_id}")

    # 최신 데이터부터 limit만큼 반환
    return {"broadcaster_id": broadcaster_id, "contexts": buffered_contexts[broadcaster_id][-limit:]}


@app.get("/status")
async def get_service_status():
    """
    ContextService의 현재 상태를 반환합니다.
    """
    redis_status = "Disconnected"
    try:
        if redis_manager and await redis_manager.redis_client.ping():
            redis_status = "Connected"
    except Exception:
        pass  # ping 실패 시 Disconnected 유지

    active_monitors = []
    try:
        if redis_manager:
            active_monitors = await redis_manager.get_all_active_monitors()
    except ConnectionError:
        active_monitors = ["Error: Redis Disconnected"]
    except Exception as e:
        active_monitors = [f"Error fetching active monitors: {e}"]

    return {
        "service_status": "running",
        "redis_connection": redis_status,
        "buffered_contexts_count": {bid: len(contexts) for bid, contexts in buffered_contexts.items()},
        "active_monitors_in_redis": active_monitors,
        "last_context_received_time": LAST_CONTEXT_RECEIVED_TIME,
    }


# --- 백그라운드 태스크: Context를 AIAnalysisService로 주기적으로 전송 (Push 방식) ---
async def send_contexts_to_ai_analysis_periodically():
    """
    일정 시간마다 버퍼링된 컨텍스트를 AIAnalysisService로 전송합니다.
    """
    print("ContextService: Starting periodic context send task.")
    while True:
        await asyncio.sleep(CONTEXT_SEND_INTERVAL_SECONDS)
        if not CONTEXT_RECEIVE_URL:
            # print("CONTEXT_RECEIVE_URL is not set. Skipping context send.")
            continue

        for broadcaster_id, contexts in list(buffered_contexts.items()):  # 순회 중 변경 방지를 위해 list()
            if not contexts:
                continue

            # 해당 방송인의 모든 컨텍스트를 가져오고 버퍼 비우기
            contexts_to_send = contexts[:]  # 현재까지 모인 모든 컨텍스트 복사
            buffered_contexts[broadcaster_id].clear()  # 버퍼 비우기

            payload = {"broadcaster_id": broadcaster_id, "contexts": contexts_to_send}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        CONTEXT_RECEIVE_URL,
                        json=payload,
                        timeout=10,  # 전송 타임아웃
                    )
                    response.raise_for_status()
                    # print(f"ContextService: Sent {len(contexts_to_send)} contexts for {broadcaster_id} to AIAnalysisService.")
            except httpx.RequestError as e:
                print(f"ContextService: Failed to send contexts for {broadcaster_id} to AIAnalysisService: {e}")
                # 실패 시 버퍼에 다시 추가할 것인지 결정 (재전송 로직)
                buffered_contexts[broadcaster_id].extend(contexts_to_send)  # 다시 추가하여 다음 주기 재전송 시도
            except Exception as e:
                print(f"ContextService: Unexpected error sending contexts for {broadcaster_id}: {e}")
                buffered_contexts[broadcaster_id].extend(contexts_to_send)  # 다시 추가


# --- 백그라운드 태스크: 모니터링 상태 확인 및 재할당 ---
async def check_and_reallocate_monitors_periodically():
    """
    주기적으로 활성 모니터링 중인 방송인이지만, 오랫동안 컨텍스트를 보내지 않는 경우를 감지하여
    모니터링 재시작을 지시합니다. (MonitorWorker 비정상 종료 감지 및 복구)
    """
    print("ContextService: Starting periodic monitor reallocation check task.")
    while True:
        await asyncio.sleep(REALLOCATION_CHECK_INTERVAL_SECONDS)

        try:
            active_monitors = await redis_manager.get_all_active_monitors()

            for broadcaster_id in active_monitors:
                last_received = LAST_CONTEXT_RECEIVED_TIME.get(broadcaster_id, 0)

                # 'OPEN' 상태이지만 일정 시간(예: 2 * WATCH_INTERVAL_SECONDS) 동안 컨텍스트를 받지 못한 경우
                # 여기서 WATCH_INTERVAL_SECONDS는 MonitorWorker가 데이터를 보내는 주기여야 합니다.
                # 임시로 2 * ContextService의 CONTEXT_SEND_INTERVAL_SECONDS로 설정
                if time.time() - last_received > 2 * CONTEXT_SEND_INTERVAL_SECONDS:
                    print(
                        f"ContextService: {broadcaster_id} is active but no context received for too long. Reallocating monitor."
                    )

                    # 다시 start_monitor 명령을 발행하여 다른 워커가 가져가도록 유도
                    # 이때 chat_channel_id가 필요할 수 있으나, 현재 ContextService에 저장되어 있지 않음.
                    # -> Redis Set에 status 외에 chatChannelId도 함께 저장하거나, Redis Hash에 방송인별 상세 정보를 저장해야 함.
                    # 임시 방편으로 chat_channel_id 없이 start 명령만 보냄. (Worker는 이 정보 없으면 시작 못할 수 있음)
                    # 실제로는 Redis에 {broadcaster_id: {status: "OPEN", chat_channel_id: "...", ...}} 형태로 저장하는 것이 좋습니다.
                    # 여기서는 일단 재시작 명령만 보냅니다.
                    await redis_manager.publish_monitor_command("start_monitor", broadcaster_id)
                    # 재할당 명령을 보냈으므로, 마지막 수신 시간을 현재 시간으로 업데이트하여 즉시 다시 트리거되지 않게 함
                    LAST_CONTEXT_RECEIVED_TIME[broadcaster_id] = time.time()

        except ConnectionError as e:
            print(f"ContextService: Redis connection lost during reallocation check: {e}")
        except Exception as e:
            print(f"ContextService: Error during reallocation check: {e}")
