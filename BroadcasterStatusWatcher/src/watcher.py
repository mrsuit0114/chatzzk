import asyncio
import json
import time

import config
import httpx
import redis_client
from enums import LiveStatus
from loguru import logger


class ChannelStatusWatcher:
    def __init__(self):
        self.current_channel_states = {}

    async def get_live_status(self, channel_id: str) -> str:
        url = f"https://api.chzzk.naver.com/polling/v2/channels/{channel_id}/live-status"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=config.HEADERS, timeout=5)
                response.raise_for_status()
                data = response.json()

                content = data.get("content")
                if not content:
                    return LiveStatus.CLOSE.value

                return content.get("status", LiveStatus.CLOSE.value)

        except Exception as e:
            logger.error(f"[{channel_id}] API Error: {e}")
            return LiveStatus.ERROR.value

    async def add_status_to_stream(self, channel_id: str, new_status: str):
        if redis_client.redis_client is None:
            logger.error("Redis not initialized.")
            return

        payload = {
            "channel_id": channel_id,
            "status": new_status,
            "timestamp": time.time(),
        }

        await redis_client.redis_client.xadd(
            config.CHZZK_LIVE_STATUS_STREAM, {"data": json.dumps(payload)}, maxlen=100, approximate=True
        )
        logger.info(f"[{channel_id}] Status {new_status} sent to stream.")

    async def watch_channel(self, channel_id: str):
        initial_status = await self.get_live_status(channel_id)
        self.current_channel_states[channel_id] = initial_status

        logger.info(f"[{channel_id}] Initial status: {initial_status}")
        if initial_status == LiveStatus.OPEN.value:
            await self.add_status_to_stream(channel_id, initial_status)

        while True:
            logger.info(f"now trying monitoring for {channel_id}")
            await asyncio.sleep(config.WATCH_INTERVAL_SECONDS)
            new_status = await self.get_live_status(channel_id)
            logger.info(f"{channel_id} status: {new_status}")

            if new_status != LiveStatus.ERROR.value and new_status != self.current_channel_states[channel_id]:
                await self.add_status_to_stream(channel_id, new_status)
                self.current_channel_states[channel_id] = new_status
