import asyncio
from datetime import datetime

from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from prefect.utilities.annotations import quote

from app.pipeline.containers import AppContainer
from chatzzk_core.schemas.config import Settings


@task(cache_policy=NO_CACHE)
async def task_get_discovery_targets(platform_service, discovery_services) -> list[dict]:
    """플랫폼 서비스와 디스커버리 서비스 목록을 주입받아 대상 채널들을 확정"""
    platform_codes = await platform_service.list_all_platform_codes()

    targets = []
    for code in platform_codes:
        service = discovery_services[code]
        channels = await service.list_active_channels()
        targets.append({"platform_code": code, "channels": channels})
    return targets


@task(cache_policy=NO_CACHE)
async def task_search_new_vods(service, target_channel: dict) -> tuple[list, datetime]:
    """특정 플랫폼 서비스 인스턴스를 주입받아 스캔 수행"""
    return await service.scan_new_vods(target_channel)


@task(cache_policy=NO_CACHE)
async def task_save_discovery_results(
    service,
    channel_id: int,
    vod_metas: list,
    scanned_at: datetime,
) -> list[int]:
    """특정 플랫폼 서비스 인스턴스를 주입받아 결과 저장"""
    return await service.save_discovery_results(channel_id, vod_metas, scanned_at)


# --- Flow: 리소스의 생명 주기를 관리합니다 ---


@flow(name="VOD Discovery", log_prints=True)
async def discovery_flow():
    # 1. Flow가 시작될 때 리소스 초기화 (크론 주기마다 새로 실행됨)
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        # 사용할 서비스 인스턴스 미리 확보
        platform_service = await container.service_package.platform_service()
        discovery_services = await container.service_package.vod_discovery_services()

        # 2. 첫 번째 Task 실행 (서비스 객체를 quote로 감싸서 전달)
        discovery_targets = await task_get_discovery_targets(quote(platform_service), quote(discovery_services))

        for target in discovery_targets:
            platform_code = target["platform_code"]
            target_channels = target["channels"]
            service = discovery_services[platform_code]

            for target_channel in target_channels:
                # 3. 개별 채널 스캔 및 저장 (동일한 서비스 객체 재사용)
                new_vods, scanned_at = await task_search_new_vods(quote(service), target_channel)
                await task_save_discovery_results(quote(service), target_channel["channel_id"], new_vods, scanned_at)

    finally:
        # 4. Flow가 끝나면(성공/실패 무관) 리소스 정리
        # 이 과정이 있어 24시간 워커 환경에서도 세션 누수가 발생하지 않습니다.
        await container.shutdown_resources()


if __name__ == "__main__":
    asyncio.run(discovery_flow())
