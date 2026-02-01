import asyncio
from enum import StrEnum

from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from prefect.utilities.annotations import quote

from app.pipeline.containers import AppContainer
from chatzzk_core.constants import PlatformCode, VODPipelineStepStatus, VODProcessingStep
from chatzzk_core.schemas.config import Settings
from chatzzk_core.schemas.internal import TargetVODInfo


class ProcessingMode(StrEnum):
    BATCH = "BATCH"  # 신규 처리
    SINGLE = "SINGLE"  # 수동 단건
    RETRY = "RETRY"  # 실패 재시도


def is_step_completed(logs: dict, step_key: str) -> bool:
    step_info = logs.get(step_key)
    if not step_info:
        return False
    return step_info.get("status") == VODPipelineStepStatus.COMPLETED


@task(cache_policy=NO_CACHE)
async def task_dispatch_vod_info(
    dispatch_service,
    mode: ProcessingMode,
    batch_size: int,
    vod_id: int | None = None,
) -> list[TargetVODInfo]:
    """
    vod_id가 있으면 해당 VOD만 가져오고 (Single Mode),
    없으면 batch_size만큼 가져옵니다 (Batch Mode).
    """
    if mode == ProcessingMode.SINGLE:
        target = await dispatch_service.get_target_vod(vod_id)
        return [target] if target else []
    elif mode == ProcessingMode.RETRY:
        return await dispatch_service.allocate_failed_batch(batch_size)
    else:
        return await dispatch_service.allocate_next_batch(batch_size)


@task(cache_policy=NO_CACHE, tags=["limit-chat-collection"])
async def task_collect_chat(service, vod_id: int, video_no: str, duration: int):
    return await service.collect_and_save_chats(vod_id, video_no, duration)


@task(cache_policy=NO_CACHE, tags=["limit-audio-collection"])
async def task_collect_audio(service, vod_id: int, video_no: str):
    return await service.collect_and_save_audio(vod_id, video_no)


@task(cache_policy=NO_CACHE, tags=["limit-perform-vad"])
async def task_perform_vad(service, vod_id: int):
    return await service.perform_vad(vod_id)


@task(cache_policy=NO_CACHE, tags=["limit-perform-asr"])
async def task_perform_asr(service, vod_id: int):
    return await service.perform_asr(vod_id)


@task(cache_policy=NO_CACHE, tags=["limit-generate-summaries"])
async def task_generate_summaries(service, vod_id: int, channel_id: int, platform_code: PlatformCode):
    await service.generate_segment_summaries(platform_code, channel_id, vod_id)
    return await service.generate_chapter_summaries(platform_code, channel_id, vod_id)


@task(cache_policy=NO_CACHE)
async def task_process_analysis(service, vod_id: int, platform_code: PlatformCode):
    return await service.process(vod_id, platform_code)


@task(cache_policy=NO_CACHE)
async def task_finalize_vod(service, vod_id: int):
    return await service.finalize_vod(vod_id)


@flow(name="Single VOD Pipeline", log_prints=True)
async def process_single_vod(vod_info: TargetVODInfo, services: dict):
    vod_id = vod_info.vod.id
    platform_code = vod_info.platform.platform_code
    video_no = vod_info.vod.video_no
    duration = vod_info.vod.duration
    channel_id = vod_info.channel.id
    logs = vod_info.pipeline_log

    print(f"Processing VOD: {vod_id} ({video_no}, {platform_code}, {duration}, {channel_id})")

    if not is_step_completed(logs, VODProcessingStep.CRAWL_CHATS):
        await task_collect_chat(quote(services["chat"][platform_code]), vod_id, video_no, duration)
    else:
        print(f"⏩ Skipping Chat Collection for {vod_id}")

    # 2. 오디오 수집
    if not is_step_completed(logs, VODProcessingStep.DOWNLOAD_AUDIO):
        await task_collect_audio(quote(services["audio"][platform_code]), vod_id, video_no)
    else:
        print(f"⏩ Skipping Audio Collection for {vod_id}")

    # 3. VAD 수행
    if not is_step_completed(logs, VODProcessingStep.PERFORM_VAD):
        await task_perform_vad(quote(services["vad"]), vod_id)

    # 4. ASR 수행
    if not is_step_completed(logs, VODProcessingStep.PERFORM_ASR):
        await task_perform_asr(quote(services["asr"]), vod_id)

    # 5. 요약 생성 (Segment & Chapter) - 보통 같이 묶여 있다면 하나만 체크하거나 둘 다 체크
    segment_done = is_step_completed(logs, VODProcessingStep.GENERATE_SEGMENT_SUMMARY)
    chapter_done = is_step_completed(logs, VODProcessingStep.GENERATE_CHAPTER_SUMMARY)

    if not (segment_done and chapter_done):
        await task_generate_summaries(quote(services["llm"]), vod_id, channel_id, platform_code)

    # 6. 분석 데이터 생성
    if not is_step_completed(logs, VODProcessingStep.GENERATE_ANALYSIS):
        await task_process_analysis(quote(services["log"]), vod_id, platform_code)

    # 7. 파이널라이즈
    await task_finalize_vod(quote(services["publish"]), vod_id)


@flow(name="VOD Processing Entrypoint", log_prints=True)
async def processing_flow(
    mode: ProcessingMode = ProcessingMode.BATCH,
    batch_size: int = 3,
    vod_id: int | None = None,
):
    container = AppContainer(settings=Settings())
    await container.init_resources()

    try:
        # 1. 서비스들을 미리 로드
        dispatch_service = await container.service_package.vod_dispatch_service()
        services = {
            "chat": await container.service_package.chat_collection_services(),
            "audio": await container.service_package.audio_collection_services(),
            "vad": await container.service_package.vad_service(),
            "asr": await container.service_package.asr_service(),
            "llm": await container.service_package.llm_generation_service(),
            "log": await container.service_package.log_analysis_service(),
            "publish": await container.service_package.vod_publishing_service(),
        }

        # 2. 배치 할당
        vod_info_list = await task_dispatch_vod_info(quote(dispatch_service), mode, batch_size, vod_id)

        if not vod_info_list:
            print("No VODs to process.")
            return

        # 3. 병렬 실행 시 서비스 뭉치를 함께 전달
        sub_flow_coroutines = [
            process_single_vod(vod_info, services)  # dict 자체는 직렬화 필요 없음 (Sub-flow 호출이므로)
            for vod_info in vod_info_list
        ]

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
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    asyncio.run(processing_flow())
