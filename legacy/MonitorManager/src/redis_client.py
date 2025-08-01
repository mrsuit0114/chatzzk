# monitor_manager/redis_client.py
import time
from typing import Optional

import redis
from models import ChannelMonitorStatus

from config import Config


class RedisClient:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
        try:
            self.client.xgroup_create(
                Config.CHZZK_LIVE_STATUS_STREAM, Config.MONITOR_MANAGER_GROUP, id="0", mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):  # 그룹이 이미 존재하는 경우는 무시
                raise e

    def get_stream_messages(self, count=10, block=2000):
        """Redis Stream에서 메시지를 가져옵니다."""
        # Consumer Group을 사용하여 메시지 읽기
        messages = self.client.xreadgroup(
            groupname=Config.MONITOR_MANAGER_GROUP,
            consumername=Config.MONITOR_MANAGER_ID,
            streams={Config.CHZZK_LIVE_STATUS_STREAM: ">"},  # '>'는 새로운 메시지부터 읽기
            count=count,
            block=block,
        )
        return messages

    def acknowledge_stream_message(self, message_id: str):
        """Redis Stream 메시지를 ACK 처리합니다."""
        self.client.xack(Config.CHZZK_LIVE_STATUS_STREAM, Config.MONITOR_MANAGER_GROUP, message_id)

    def set_channel_monitor_status(
        self, status: ChannelMonitorStatus
    ):  # 있으면 모니터링 중인거고 없으면 진행중이 아니기 떄문에 channel_id와 디플로이먼트를 관리하기 위한 정보면 충분분
        """채널 모니터링 상태를 Redis에 저장합니다."""
        key = f"channel_monitor_status:{status.channel_id}"
        self.client.set(key, status.to_json())

    def get_channel_monitor_status(self, channel_id: str) -> Optional[ChannelMonitorStatus]:
        """Redis에서 채널 모니터링 상태를 가져옵니다."""
        key = f"channel_monitor_status:{channel_id}"
        data = self.client.get(key)
        if data:
            return ChannelMonitorStatus.from_json(data)
        return None

    def delete_channel_monitor_status(self, channel_id: str):
        """Redis에서 채널 모니터링 상태를 삭제합니다."""
        key = f"channel_monitor_status:{channel_id}"
        self.client.delete(key)

    def acquire_lock(self, lock_name: str, acquire_timeout: int = 5, lock_timeout: int = 10) -> Optional[str]:
        """
        분산 락을 획득합니다. (Redlock 알고리즘의 단순화된 구현)
        lock_name: 락 이름 (예: channel_id)
        acquire_timeout: 락 획득 시도 최대 시간 (초)
        lock_timeout: 락 유지 시간 (초)

        Returns: 락을 획득했을 경우 락 값 (고유 ID), 실패 시 None
        """
        identifier = str(time.time()) + "-" + Config.MONITOR_MANAGER_ID  # 고유 ID
        lock_key = f"lock:{lock_name}"
        end_time = time.time() + acquire_timeout

        while time.time() < end_time:
            if self.client.set(lock_key, identifier, nx=True, ex=lock_timeout):
                return identifier
            time.sleep(0.1)
        return None

    def release_lock(self, lock_name: str, identifier: str) -> bool:
        """
        획득한 분산 락을 해제합니다.
        락 획득 시 사용된 고유 ID와 일치할 경우에만 해제합니다.
        """
        lock_key = f"lock:{lock_name}"
        pipeline = self.client.pipeline()
        pipeline.watch(lock_key)  # 락 키 변경 감시
        if pipeline.get(lock_key).decode("utf-8") == identifier:
            pipeline.multi()
            pipeline.delete(lock_key)
            pipeline.execute()
            return True
        else:
            pipeline.unwatch()
            return False

    # def get_pending_messages(self):
    #     """처리되지 않은 (pending) 메시지를 가져옵니다. 다른 monitor_manager가 죽었을 경우를 대비."""
    #     pending_entries = self.client.xpending(Config.CHZZK_LIVE_STATUS_STREAM, Config.MONITOR_MANAGER_GROUP)
    #     # pending_entries는 {'pending': num, 'min': id, 'max': id, 'consumers': [{name, pending}]} 형태
    #     # 실제 메시지 내용은 XCLAIM이나 XREADGROUP으로 다시 가져와야 함.
    #     # 여기서는 단순히 pending 메시지가 있음을 알리는 용도로 사용하거나,
    #     # 더 나아가 XAUTOCLAIM을 사용하여 자동으로 claim할 수도 있습니다.
    #     if pending_entries and pending_entries['pending'] > 0:
    #         print(f"Pending messages found: {pending_entries['pending']}")
    #         # 실제 메시지를 가져오기 위해 XCLAIM 또는 XREADGROUP으로 다시 읽는 로직 추가 필요
    #         # 예: self.client.xreadgroup(...) 또는 self.client.xclaim(...)
    #     return pending_entries

    def get_all_channel_monitor_statuses(self) -> dict[str, ChannelMonitorStatus]:
        """Redis에 저장된 모든 채널 모니터링 상태를 가져옵니다."""
        statuses = {}
        for key in self.client.scan_iter("channel_monitor_status:*"):
            channel_id = key.split(":")[1]
            status = self.get_channel_monitor_status(channel_id)
            if status:
                statuses[channel_id] = status
        return statuses
