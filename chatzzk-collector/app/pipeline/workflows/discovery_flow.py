import asyncio
from datetime import datetime

from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from app.pipeline.containers import AppContainer
from chatzzk_core.constants import PlatformCode
from chatzzk_core.schemas.config import Settings


@task(cache_policy=NO_CACHE)
async def task_list_platform_codes() -> list[str]:
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.platform_service()
        return await service.list_all_platform_codes()
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE)
async def task_scan_target_channels(platform_code: PlatformCode) -> list[dict]:
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service_dict = await container.service_package.vod_discovery_services()
        service = service_dict[platform_code]
        return await service.list_active_channels()
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE)
async def task_search_new_vods(platform_code: PlatformCode, target_channel: dict) -> tuple[list, datetime]:
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service_dict = await container.service_package.vod_discovery_services()
        service = service_dict[platform_code]
        return await service.scan_new_vods(target_channel)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE)
async def task_save_discovery_results(
    platform_code: PlatformCode,
    channel_id: int,
    vod_metas: list,
    scanned_at: datetime,
) -> list[int]:
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service_dict = await container.service_package.vod_discovery_services()
        service = service_dict[platform_code]
        return await service.save_discovery_results(channel_id, vod_metas, scanned_at)
    finally:
        await container.shutdown_resources()


@flow(name="VOD Discovery", log_prints=True)
async def discovery_flow():
    platform_codes = await task_list_platform_codes()
    print(platform_codes)

    for platform_code in platform_codes:
        target_channels = await task_scan_target_channels(platform_code)
        for target_channel in target_channels:
            print(target_channel)
            new_vods, scanned_at = await task_search_new_vods(platform_code, target_channel)
            await task_save_discovery_results(platform_code, target_channel["channel_id"], new_vods, scanned_at)


if __name__ == "__main__":
    asyncio.run(discovery_flow())
