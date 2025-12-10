from datetime import datetime, UTC
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_constants.service_codes import FileKeyTemplate

from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.repositories.channel import ChannelRepository
from chatzzk_data_access.storages.base import PipelineStorage

from typing import AsyncGenerator
from pydantic import TypeAdapter
from chatzzk_clients.llm.prompt_builder import PromptBuilder
from chatzzk_clients.llm.litellm_proxy_client import LiteLLMProxyClient
from chatzzk_schemas.storage.models import StreamEntry, get_stream_entry_adapter
from chatzzk_constants.service_codes import StreamContextWindowSize
from chatzzk_schemas.api_models.llm import PlatformMetadata, ChannelMetadata, StreamSegmentAnalysisResponse
from chatzzk_schemas.dto.api.core.vod import SummaryGenerateRequestDTO, SummaryGenerateResponseDTO
from chatzzk_schemas.dto.repo_params.core.vod import get_vod_find_params
from chatzzk_data_access.repositories.platform import PlatformRepository
from chatzzk.services.interfaces.llm_generation import LLMGenerationInterface
from chatzzk_constants.service_codes import LLMTask, VODProcessingStepStatus, VODProcessingStep
from chatzzk_schemas.storage.models import SummaryRawEntry


async def _get_broadcast_logs(
    chat_entries_agen: AsyncGenerator[dict, None],
    asr_entries_agen: AsyncGenerator[dict, None],
    window_size: int,
    adapter: TypeAdapter[StreamEntry],
) -> AsyncGenerator[tuple[int, int, list[StreamEntry]], None]:
    # 1. 두 비동기 제너레이터를 병합하여 시간순으로 정렬된 단일 스트림 생성
    async def merged_stream():
        chat_iter = chat_entries_agen.__aiter__()
        asr_iter = asr_entries_agen.__aiter__()

        async def get_validated_next(iterator):
            try:
                item = await anext(iterator)
                return adapter.validate_python(item)
            except StopAsyncIteration:
                return None

        chat_item = await get_validated_next(chat_iter)
        asr_item = await get_validated_next(asr_iter)

        while chat_item is not None or asr_item is not None:
            if chat_item is not None and asr_item is not None:
                if chat_item.timestamp <= asr_item.timestamp:
                    yield chat_item
                    chat_item = await get_validated_next(chat_iter)
                else:
                    yield asr_item
                    asr_item = await get_validated_next(asr_iter)
            elif chat_item is not None:
                yield adapter.validate_python(chat_item)
                chat_item = await anext(chat_iter, None)
            else:
                yield adapter.validate_python(asr_item)
                asr_item = await anext(asr_iter, None)

    # 2. 윈도우 단위로 그룹핑 (Tumbling Window)
    current_window = []
    window_start = 0

    async for entry in merged_stream():
        # 현재 엔트리가 윈도우 범위를 벗어나면, 벗어날 때까지 윈도우를 이동하며 yield
        while entry.timestamp >= window_start + window_size:
            if current_window:
                yield window_start, window_start + window_size, current_window
            current_window = []
            window_start += window_size

        current_window.append(entry)

    # 남은 데이터 반환
    if current_window:
        yield window_start, window_start + window_size, current_window


class LLMGenerationService(LLMGenerationInterface):
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        tmp_storage: PipelineStorage,
        vod_repo: VODRepository,
        channel_repo: ChannelRepository,
        platform_repo: PlatformRepository,
        prompt_builder: PromptBuilder,
        llm_client: LiteLLMProxyClient,
    ):
        self.db_session_factory = db_session_factory
        self.tmp_storage = tmp_storage
        self.vod_repo = vod_repo
        self.channel_repo = channel_repo
        self.platform_repo = platform_repo
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.summary_window_size = StreamContextWindowSize.SUMMARY
        self.meta_summary_window_size = StreamContextWindowSize.META_SUMMARY

    async def generate_summary(self, dto: SummaryGenerateRequestDTO) -> SummaryGenerateResponseDTO:
        platform_code = dto.platform_code
        video_no = dto.video_no
        summary_raw_key = FileKeyTemplate.get_summary_raw_key(platform_code, video_no)
        start_time = datetime.now(UTC)

        async with self.db_session_factory() as session:
            async with session.begin():
                # 1. 완료 여부 확인
                if await self._check_completion_status(session, dto):
                    return SummaryGenerateResponseDTO(
                        summary_raw_key=summary_raw_key, summary_raw_result=VODProcessingStepStatus.COMPLETED
                    )

                # 2. 메타데이터 조회
                platform_metadata, channel_metadata = await self._fetch_metadata(session, dto)

        try:
            # 3. 복구 상태 로드
            last_end_time, previous_summary = await self._load_recovery_state(summary_raw_key)

            # 4. 로그 데이터 로드
            asr_key = FileKeyTemplate.get_asr_key(platform_code, video_no)
            chat_key = FileKeyTemplate.get_chat_key(platform_code, video_no)

            chat_entries_gen = await self.tmp_storage.load_jsonl(chat_key)
            asr_entries_gen = await self.tmp_storage.load_jsonl(asr_key)

            broadcast_logs_gen = _get_broadcast_logs(
                chat_entries_gen, asr_entries_gen, self.summary_window_size, get_stream_entry_adapter(platform_code)
            )

            # 5. 요약 생성 루프
            async for start, end, logs in broadcast_logs_gen:
                if end <= last_end_time:
                    continue

                prompt_messages = self.prompt_builder.get_summary_prompt(
                    platform_metadata=platform_metadata,
                    channel_metadata=channel_metadata,
                    previous_summary=previous_summary if previous_summary else None,
                    broadcast_logs=logs,
                )

                try:
                    response_str = await self.llm_client.generate(
                        messages=prompt_messages,
                        model=LLMTask.SUMMARIZE,
                        schema_model=StreamSegmentAnalysisResponse,
                    )

                    segment_result = StreamSegmentAnalysisResponse.model_validate_json(response_str)
                    previous_summary = segment_result.summary

                    entry = segment_result.to_summary_raw_entry(start, end)

                    async def single_entry_generator():
                        yield entry.model_dump()

                    await self.tmp_storage.append_jsonl(summary_raw_key, single_entry_generator())

                except Exception as e:
                    logger.error(f"Failed to generate summary for a segment: {e}")
                    await self._update_process_status(dto, VODProcessingStepStatus.FAILED, start_time)
                    return SummaryGenerateResponseDTO(
                        summary_raw_key=summary_raw_key, summary_raw_result=VODProcessingStepStatus.FAILED
                    )

            # 6. 완료 상태 업데이트
            await self._update_process_status(dto, VODProcessingStepStatus.COMPLETED, start_time)
            return SummaryGenerateResponseDTO(
                summary_raw_key=summary_raw_key, summary_raw_result=VODProcessingStepStatus.COMPLETED
            )

        except Exception as e:
            logger.error(f"Failed to generate summary raw: {e}")
            await self._update_process_status(dto, VODProcessingStepStatus.FAILED, start_time)
            return SummaryGenerateResponseDTO(
                summary_raw_key=summary_raw_key, summary_raw_result=VODProcessingStepStatus.FAILED
            )

    async def _check_completion_status(self, session: AsyncSession, dto: SummaryGenerateRequestDTO) -> bool:
        vod_find_params = get_vod_find_params(**dto.model_dump())
        unified_vod = await self.vod_repo.find_vod_with_platform_vod(session, dto.platform_code, vod_find_params)
        vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)
        detail = vod.vod_processing_status_detail.status_details or {}
        return detail.get(VODProcessingStep.GENERATE_SUMMARY, {}).get("status") == VODProcessingStepStatus.COMPLETED

    async def _fetch_metadata(
        self, session: AsyncSession, dto: SummaryGenerateRequestDTO
    ) -> tuple[PlatformMetadata, ChannelMetadata]:
        platform = await self.platform_repo.find_by_platform_code(session, dto.platform_code)
        vod_find_params = get_vod_find_params(**dto.model_dump())
        vod = await self.vod_repo.find_vod_with_platform_vod(session, dto.platform_code, vod_find_params)
        channel = await self.channel_repo.find_channel_with_channel_metadata(session, vod.channel_id)
        metadata = channel.channel_metadata.metadata_description

        platform_metadata = PlatformMetadata(platform_name=platform.platform_name, donation_unit=platform.donation_unit)
        channel_metadata = ChannelMetadata(**metadata)
        return platform_metadata, channel_metadata

    async def _load_recovery_state(self, summary_raw_key: str) -> tuple[int, str]:
        last_end_time = 0
        previous_summary = ""
        try:
            existing_summaries = await self.tmp_storage.load_jsonl(summary_raw_key)
            async for entry in existing_summaries:
                summary_entry = SummaryRawEntry.model_validate(entry)
                last_end_time = summary_entry.end
                previous_summary = summary_entry.summary
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Failed to load existing summary raw: {e}")
        return last_end_time, previous_summary

    async def _update_process_status(
        self, dto: SummaryGenerateRequestDTO, status: VODProcessingStepStatus, start_time: datetime
    ):
        end_time = datetime.now(UTC)
        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = get_vod_find_params(**dto.model_dump())
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(
                    session, dto.platform_code, vod_find_params
                )
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)

                await self.vod_repo.update_processing_detail(
                    session,
                    vod,
                    step=VODProcessingStep.GENERATE_SUMMARY,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                )
