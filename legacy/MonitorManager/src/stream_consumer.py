# stream_consumer.py
import json
import time

from loguru import logger
from monitor_manager import MonitorManager
from redis_client import RedisClient

from config import Config


class StreamConsumer:
    def __init__(self, redis_client: RedisClient, monitor_manager: MonitorManager):
        self.redis_client = redis_client
        self.monitor_manager = monitor_manager

    def run(self):
        logger.info(f"Monitor Manager {Config.MONITOR_MANAGER_ID} started listening to Redis Stream.")
        # self.monitor_manager.recover_from_failure() # 시작 시 복구 프로세스 실행

        while True:
            try:
                logger.info("try message")
                messages = self.redis_client.get_stream_messages()
                if messages:
                    logger.info("got message")
                    for stream_name, message_list in messages:
                        for message_id, message_data in message_list:
                            self.handle_stream_message(message_id, message_data)
                else:
                    time.sleep(1)  # 메시지가 없으면 잠시 대기

            except Exception as e:
                logger.error(f"Error consuming stream: {e}")
                time.sleep(5)  # 에러 발생 시 잠시 후 재시도

    def handle_stream_message(self, message_id: str, message_data: dict):
        """
        Redis Stream에서 받은 메시지를 처리합니다.
        """
        try:
            # 1. 'data' 키에서 실제 JSON 바이트 문자열 추출
            raw_json_bytes = message_data.get(b"data")  # Redis는 종종 키를 바이트로 반환합니다.

            if not raw_json_bytes:
                logger.info(f"Invalid message format: Missing 'data' key in {message_data}. Skipping.")
                self.redis_client.acknowledge_stream_message(message_id)
                return

            # 2. 바이트 문자열을 UTF-8로 디코딩
            json_string = raw_json_bytes.decode("utf-8")

            # 3. JSON 문자열을 파싱하여 파이썬 딕셔너리로 변환
            parsed_data = json.loads(json_string)

            # 이제 파싱된 딕셔너리에서 'type'과 'channel_id'를 추출
            request_type = parsed_data.get("status")
            channel_id = parsed_data.get("channel_id")

            if not request_type or not channel_id:
                logger.info(
                    f"Invalid message format: Missing 'status' or 'channel_id' in parsed data {parsed_data}. Skipping."
                )
                self.redis_client.acknowledge_stream_message(message_id)
                return

            logger.info(f"Received message: ID={message_id}, Type={request_type}, Channel={channel_id}")

            if request_type == "OPEN":
                self.monitor_manager.start_monitoring(channel_id)
            elif request_type == "CLOSE":
                self.monitor_manager.stop_monitoring(channel_id)
            else:
                logger.warning(f"Unknown request type: {request_type}. Skipping.")

            self.redis_client.acknowledge_stream_message(message_id)  # 성공적으로 처리 후 ACK
            logger.info(f"Message {message_id} for channel {channel_id} processed and acknowledged.")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error for message {message_id}: {e} - Data: {message_data}")
            # JSON 파싱 오류는 재시도가 필요할 수 있으므로 ACK하지 않을 수 있습니다.
            # 하지만 무한 루프를 방지하기 위해 max_retries 같은 로직을 고려해야 합니다.
            # 여기서는 일단 ACK를 보내지 않습니다.
        except Exception as e:
            logger.error(f"Error handling message {message_id} for channel {channel_id}: {e}", exc_info=True)
            # 다른 종류의 오류 발생 시에도 ACK를 보내지 않아 다음에 다시 처리될 수 있도록 함
