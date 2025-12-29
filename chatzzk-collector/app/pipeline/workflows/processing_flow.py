import asyncio

from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from app.pipeline.containers import AppContainer
from chatzzk_core.constants import PlatformCode
from chatzzk_core.schemas.config import Settings
from chatzzk_core.schemas.internal import TargetVODInfo

PROCESSING_BATCH_SIZE = 5


@task(cache_policy=NO_CACHE)
async def task_dispatch_vod_info() -> list[TargetVODInfo]:
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.vod_dispatch_service()
        return await service.allocate_next_batch(PROCESSING_BATCH_SIZE)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE, tags=["limit-chat-collection"])
async def task_collect_chat(vod_id: int, platform_code: PlatformCode, video_no: str, duration: int):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service_dict = await container.service_package.chat_collection_services()
        service = service_dict[platform_code]
        return await service.collect_and_save_chats(vod_id, video_no, duration)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE, tags=["limit-audio-collection"])
async def task_collect_audio(vod_id: int, platform_code: PlatformCode, video_no: str):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service_dict = await container.service_package.audio_collection_services()
        service = service_dict[platform_code]
        return await service.collect_and_save_audio(vod_id, video_no)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE, tags=["limit-perform-vad"])
async def task_perform_vad(vod_id: int):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.vad_service()
        return await service.perform_vad(vod_id)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE, tags=["limit-perform-asr"])
async def task_perform_asr(vod_id: int):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.asr_service()
        return await service.perform_asr(vod_id)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE, tags=["limit-generate-summaries"])
async def task_generate_summaries(vod_id: int, channel_id: int, platform_code: PlatformCode):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.llm_generation_service()
        await service.generate_segment_summaries(platform_code, channel_id, vod_id)
        return await service.generate_chapter_summaries(platform_code, channel_id, vod_id)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE)
async def task_process_analytics(vod_id: int, platform_code: PlatformCode):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.log_analytics_service()
        return await service.process(vod_id, platform_code)
    finally:
        await container.shutdown_resources()


@task(cache_policy=NO_CACHE)
async def task_finalize_vod(vod_id: int):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        service = await container.service_package.vod_publishing_service()
        return await service.finalize_vod(vod_id)
    finally:
        await container.shutdown_resources()


@flow(name="Single VOD Pipeline", log_prints=True)
async def process_single_vod(vod_info: TargetVODInfo):
    vod_id = vod_info.vod.id
    platform_code = vod_info.platform.platform_code
    video_no = vod_info.vod.video_no
    duration = vod_info.vod.duration
    channel_id = vod_info.channel.id

    await task_collect_chat(vod_id, platform_code, video_no, duration)
    await task_collect_audio(vod_id, platform_code, video_no)
    await task_perform_vad(vod_id)
    await task_perform_asr(vod_id)
    await task_generate_summaries(vod_id, channel_id, platform_code)
    await task_process_analytics(vod_id, platform_code)
    await task_finalize_vod(vod_id)


@flow(name="VOD Processing Entrypoint", log_prints=True)
async def vod_processing_flow():
    vod_info_list = await task_dispatch_vod_info()

    if not vod_info_list:
        print("No VODs to process.")
        return

    print(f"🚀 Starting parallel processing for {len(vod_info_list)} VODs...")

    # 1. Coroutine 리스트 생성 (아직 실행 안 됨)
    sub_flow_coroutines = [process_single_vod(vod_info) for vod_info in vod_info_list]

    # 2. asyncio.gather로 동시 실행 및 결과 대기
    # return_exceptions=True: 하나가 실패해도 멈추지 않고, 에러 객체를 결과 리스트에 포함시킴
    results = await asyncio.gather(*sub_flow_coroutines, return_exceptions=True)

    successful = []
    failed = []

    # 3. 결과 분류 (Exception 타입인지 확인)
    for result in results:
        if isinstance(result, Exception):
            failed.append(result)
            print(f"❌ Sub-flow failed with error: {result}")
        else:
            successful.append(result)

    print(f"✅ Processed {len(successful)} items successfully")
    if failed:
        print(f"⚠️ Failed to process {len(failed)} items")


if __name__ == "__main__":
    asyncio.run(vod_processing_flow())
