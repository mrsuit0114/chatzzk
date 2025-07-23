import config
from loguru import logger

import redis.asyncio as redis

redis_client = None


async def initialize_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(config.REDIS_URL)
        await redis_client.ping()
        logger.info(f"Redis client initialized and connected to {config.REDIS_URL}")


async def close_redis_client():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis client closed.")
        redis_client = None
