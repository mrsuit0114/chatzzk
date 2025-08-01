import asyncio

import redis_client
from loguru import logger
from watcher import ChannelStatusWatcher

import config


async def main():
    await redis_client.initialize_redis_client()

    if not config.CHANNEL_IDS_TO_WATCH:
        logger.warning("No CHANNEL_IDS configured.")
        await redis_client.close_redis_client()
        return

    watcher = ChannelStatusWatcher()
    tasks = [watcher.watch_channel(cid) for cid in config.CHANNEL_IDS_TO_WATCH]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        asyncio.run(redis_client.close_redis_client())
