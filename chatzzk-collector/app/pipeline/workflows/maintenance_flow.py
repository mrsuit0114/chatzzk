import asyncio

from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from app.pipeline.containers import AppContainer
from chatzzk_core.schemas.config import Settings


@task(cache_policy=NO_CACHE)
async def task_cleanup_zombies(dispatch_service, threshold_minutes: int):
    processed_ids = await dispatch_service.mark_stale_processing_vods_as_failed(threshold_minutes)

    if processed_ids:
        print(f"Cleaned up {len(processed_ids)} zombie VODs.")


@flow(name="Maintenance: Zombie Cleanup")
async def maintenance_flow(threshold_minutes: int = 60):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        dispatch_service = await container.service_package.vod_dispatch_service()
        await task_cleanup_zombies(dispatch_service, threshold_minutes)
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    asyncio.run(maintenance_flow())
