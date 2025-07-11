import redis.asyncio as redis
from redis.exceptions import ConnectionError


class RedisManager:
    """
    Redis Set (활성 모니터링 관리) 및 Redis Stream (워커 지시) 관리를 위한 클래스.
    """

    def __init__(self, host: str, port: int, db: int, monitor_request_stream: str):
        self.redis_client = None
        self.host = host
        self.port = port
        self.db = db
        self.monitor_request_stream = monitor_request_stream
        self.active_monitor_set_key = "active_monitors"  # Redis Set의 키 이름

    async def connect(self):
        """Redis 클라이언트를 연결합니다."""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,  # 응답을 자동으로 문자열로 디코딩
                )
                await self.redis_client.ping()
                print("ContextService: Successfully connected to Redis.")
            except ConnectionError as e:
                print(f"ContextService: Failed to connect to Redis: {e}")
                self.redis_client = None  # 연결 실패 시 클라이언트 초기화
                raise

    async def disconnect(self):
        """Redis 클라이언트를 연결 해제합니다."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            print("ContextService: Disconnected from Redis.")

    async def is_broadcaster_active(self, broadcaster_id: str) -> bool:
        """주어진 방송인이 현재 활성 모니터링 목록에 있는지 확인합니다."""
        if not self.redis_client:
            raise ConnectionError("Redis client not connected.")
        return await self.redis_client.sismember(self.active_monitor_set_key, broadcaster_id)

    async def add_active_monitor(self, broadcaster_id: str) -> bool:
        """활성 모니터링 Set에 방송인을 추가합니다. 새로 추가되면 True 반환."""
        if not self.redis_client:
            raise ConnectionError("Redis client not connected.")
        added = await self.redis_client.sadd(self.active_monitor_set_key, broadcaster_id)
        return added == 1

    async def remove_active_monitor(self, broadcaster_id: str) -> bool:
        """활성 모니터링 Set에서 방송인을 제거합니다. 제거되면 True 반환."""
        if not self.redis_client:
            raise ConnectionError("Redis client not connected.")
        removed = await self.redis_client.srem(self.active_monitor_set_key, broadcaster_id)
        return removed == 1

    async def get_all_active_monitors(self) -> list[str]:
        """현재 활성 모니터링 중인 모든 방송인 ID 목록을 가져옵니다."""
        if not self.redis_client:
            raise ConnectionError("Redis client not connected.")
        members = await self.redis_client.smembers(self.active_monitor_set_key)
        return list(members)

    async def publish_monitor_command(self, command_type: str, broadcaster_id: str, **kwargs):
        """
        Redis Stream에 모니터링 명령 (start/stop)을 발행합니다.
        command_type: "start_monitor" 또는 "stop_monitor"
        """
        if not self.redis_client:
            raise ConnectionError("Redis client not connected.")

        message = {
            "type": command_type,
            "broadcaster_id": broadcaster_id,
            **kwargs,  # chat_channel_id 등 추가 데이터
        }
        await self.redis_client.xadd(self.monitor_request_stream, message)
        print(f"ContextService: Published '{command_type}' command for {broadcaster_id} to Redis Stream.")
