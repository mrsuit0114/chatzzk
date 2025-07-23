from loguru import logger

from kubernetes_client import KubernetesClient
from models import ChannelMonitorStatus
from redis_client import RedisClient


class MonitorManager:
    def __init__(self, k8s_client: KubernetesClient, redis_client: RedisClient):
        self.k8s_client = k8s_client
        self.redis_client = redis_client

    def start_monitoring(self, channel_id: str):
        """
        새로운 채널 모니터링을 시작합니다.
        1. 분산 락 획득 (다른 monitor_manager와의 중복 처리 방지)
        2. Deployment 생성
        3. Redis에 상태 저장
        4. 락 해제
        """
        deployment_name = f"monitor-{channel_id}-deployment"
        lock_name = f"channel_lock:{channel_id}"

        lock_id = self.redis_client.acquire_lock(lock_name)
        if not lock_id:
            logger.info(f"Failed to acquire lock for channel_id: {channel_id}. Another manager might be handling it.")
            return

        try:
            # Redis에 이미 해당 채널의 모니터링 상태가 있는지 확인
            existing_status = self.redis_client.get_channel_monitor_status(channel_id)
            if existing_status:
                logger.info(f"Monitoring for channel_id: {channel_id} is already running. Skipping.")
                return

            logger.info(f"Starting monitoring for channel_id: {channel_id}")
            self.k8s_client.create_monitoring_deployment(channel_id, deployment_name)

            # Redis에 상태 저장 (이 monitor_manager가 담당함을 명시)
            status = ChannelMonitorStatus(
                channel_id=channel_id,
                deployment_name=deployment_name,
            )
            self.redis_client.set_channel_monitor_status(status)
            logger.info(f"Deployment '{deployment_name}' created and status saved to Redis.")

        except Exception as e:
            logger.exception(f"Error starting monitoring for {channel_id}: {e}")
            # 에러 발생 시 락 해제 및 잠재적으로 Deployment 롤백 로직 추가
        finally:
            if lock_id:
                self.redis_client.release_lock(lock_name, lock_id)

    def stop_monitoring(self, channel_id: str):
        """
        채널 모니터링을 중지합니다.
        1. 분산 락 획득
        2. Redis에서 상태 확인 (현재 monitor_manager가 담당하는지)
        3. Deployment 삭제 (Graceful Shutdown)
        4. Redis에서 상태 삭제
        5. 락 해제
        """
        deployment_name = f"monitor-{channel_id}-deployment"
        lock_name = f"channel_lock:{channel_id}"

        lock_id = self.redis_client.acquire_lock(lock_name)
        if not lock_id:
            logger.info(f"Failed to acquire lock for channel_id: {channel_id}. Another manager might be handling it.")
            return

        try:
            status = self.redis_client.get_channel_monitor_status(channel_id)
            if not status:
                logger.info(f"Monitoring status for channel_id: {channel_id} not found in Redis. Skipping stop.")
                return

            logger.info(f"Stopping monitoring for channel_id: {channel_id}")
            self.k8s_client.delete_monitoring_deployment(deployment_name)

            # Redis에서 상태 삭제
            self.redis_client.delete_channel_monitor_status(channel_id)
            logger.info(f"Deployment '{deployment_name}' deletion requested and status removed from Redis.")

        except Exception as e:
            logger.error(f"Error stopping monitoring for {channel_id}: {e}")
        finally:
            if lock_id:
                self.redis_client.release_lock(lock_name, lock_id)

    # def recover_from_failure(self):
    #     """
    #     monitor_manager가 재시작되었을 때, 이전에 처리하던 작업들을 복구합니다.
    #     Redis에 저장된 모든 channel_monitor_status를 확인하고,
    #     현재 monitor_manager가 담당하는 Deployment들이 실제로 존재하는지 확인합니다.
    #     """
    #     print("Starting recovery process...")
    #     all_statuses = self.redis_client.get_all_channel_monitor_statuses()

    #     for channel_id, status in all_statuses.items():
    #         if status.monitor_manager_id == Config.MONITOR_MANAGER_ID:
    #             # 이 monitor_manager가 담당하던 Deployment
    #             deployment = self.k8s_client.get_deployment_status(status.deployment_name)
    #             if not deployment:
    #                 print(f"Recovery: Deployment for {channel_id} (managed by me) not found. Recreating...")
    #                 # Deployment가 존재하지 않으면 다시 생성 시도
    #                 self.start_monitoring(channel_id) # start_monitoring은 락을 획득하고 중복 생성 방지 로직이 있음
    #             else:
    #                 print(f"Recovery: Deployment for {channel_id} (managed by me) found and is active.")
    #         else:
    #             # 다른 monitor_manager가 담당하던 Deployment
    #             # 이 경우, 다른 monitor_manager가 죽었을 때 이 monitor_manager가 인계받을지 결정해야 함
    #             # TODO: 여기서는 단순하게 다른 매니저의 작업은 건드리지 않음.
    #             #       더 복잡한 장애 복구 로직 (예: 일정 시간동안 락이 해제되지 않았으면 강제로 인계)은 필요에 따라 추가.
    #             print(f"Recovery: Channel {channel_id} is managed by another manager ({status.monitor_manager_id}).")

    #     # Redis Stream의 Pending 메시지 처리
    #     # 다른 monitor_manager가 처리하다 죽은 메시지 처리
    #     pending_messages_info = self.redis_client.get_pending_messages()
    #     # 실제 pending 메시지를 가져와서 처리하는 로직 추가 필요
    #     # self.redis_client.client.xreadgroup(...) 또는 self.redis_client.client.xclaim(...) 사용
    #     # 이 부분은 Redis Stream의 Consumer Group 메커니즘을 더 깊이 이해하고 구현해야 합니다.
    #     # 예시: `self.handle_stream_message`를 재사용하여 처리
    #     print("Recovery process completed.")
