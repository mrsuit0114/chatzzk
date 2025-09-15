from loguru import logger

from chatzzk.packages.data_access import database
from chatzzk.services.collector.jobs.tasks.discovery import discover_new_vods_for_channel
from chatzzk.services.collector.jobs.tasks.processing import process_vod_to_context


def trigger_vod_discovery():
    """[Scheduler Job] 활성화된 채널에 대한 VOD 탐색 Task를 생성합니다."""
    logger.info("📡 Triggering VOD discovery tasks...")
    with database.get_db_session() as db:
        active_channels = database.get_active_channels(db)

    if not active_channels:
        logger.info("No active channels found. Nothing to do.")
        return

    for channel in active_channels:
        discover_new_vods_for_channel.delay(channel.channel_id)

    logger.info(f"Dispatched {len(active_channels)} discovery tasks.")


def trigger_vod_processing():
    """[Scheduler Job] 처리가 필요한 VOD에 대한 처리 Task를 생성합니다."""
    logger.info("📡 Triggering VOD processing tasks...")
    with database.get_db_session() as db:
        vods_to_process = database.get_vods_to_process(db, limit=20)  # 한번에 너무 많이 가져오지 않도록 제한

    for vod in vods_to_process:
        process_vod_to_context.delay(vod.id)

    logger.info(f"Dispatched {len(vods_to_process)} processing tasks.")
