from collections.abc import AsyncIterable

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.llm import ContextAssembler, LLMClient, PromptManager
from chatzzk_core.constants import (
    LLMTask,
    PlatformCode,
    StoragePaths,
    StreamAtmosphere,
    VODPipelineStepStatus,
    VODProcessingStep,
)
from chatzzk_core.schemas.config.services import LLMGenerationConfig
from chatzzk_core.schemas.internal import (
    ASREntry,
    BaseStreamEntry,
    ChannelMetadataContext,
    ChapterSummaryEntry,
    ChapterSummaryGenerationInput,
    ChapterSummaryGenerationOutput,
    ChatEntry,
    ChzzkChatEntry,
    EvaluationScores,
    PlatformMetadataContext,
    SegmentSummaryEntry,
    SegmentSummaryGenerationInput,
    SegmentSummaryGenerationOutput,
)
from chatzzk_data_access.repositories import ChannelRepository, PlatformRepository, VODRepository
from chatzzk_data_access.storages import LocalStorage


class LLMGenerationService(BasePipelineService):
    def __init__(
        self,
        tmp_storage: LocalStorage,
        platform_repo: PlatformRepository,
        channel_repo: ChannelRepository,
        vod_repo: VODRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
        context_assembler: ContextAssembler,
        prompt_manager: PromptManager,
        llm_client: LLMClient,
        config: LLMGenerationConfig,
    ):
        super().__init__(vod_repo, db_session_factory)
        self.tmp_storage = tmp_storage
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.channel_repo = channel_repo
        self.platform_repo = platform_repo
        self.context_assembler = context_assembler
        self.prompt_manager = prompt_manager
        self.llm_client = llm_client

        self.window_config = config.stream_window_config
        self.prompt_paths = config.prompt_paths

    async def _recover_last_segment_summary(self, vod_id: int) -> SegmentSummaryEntry | None:
        segment_summary_key = StoragePaths.get_segment_summary_key(vod_id)

        try:
            entries = await self.tmp_storage.read_jsonl(segment_summary_key)
        except FileNotFoundError:
            return None

        if entries:
            last_data = entries[-1]
            last_entry = SegmentSummaryEntry.model_validate(last_data)
            return last_entry

        return None

    async def _fetch_metadata_context(
        self, platform_code: PlatformCode, channel_id: int
    ) -> tuple[PlatformMetadataContext, ChannelMetadataContext]:
        async with self.db_session_factory() as session:
            platform = await self.platform_repo.get_platform_by_code(session, platform_code)
            channel_metadata = await self.channel_repo.get_channel_metadata_by_channel_id(session, channel_id)
            platform_metadata_context = PlatformMetadataContext.model_validate(platform)
            channel_metadata_context = ChannelMetadataContext.model_validate(channel_metadata)
            return platform_metadata_context, channel_metadata_context

    async def _create_log_stream_iterators(
        self, vod_id: str, platform_code: PlatformCode
    ) -> list[AsyncIterable[BaseStreamEntry]]:
        """
        [Segment Summary용]
        Chat 로그와 ASR 로그 파일을 읽어 스트림(Iterator) 리스트를 생성합니다.
        ContextAssembler.get_windows()의 입력으로 사용됩니다.
        """
        iterators: list[AsyncIterable[BaseStreamEntry]] = []

        # 1. Chat Logs 스트림 준비
        chat_model_cls: type[BaseStreamEntry]

        if platform_code == PlatformCode.CHZZK:
            chat_model_cls = ChzzkChatEntry
        # elif platform_code == PlatformCode.SOOP:
        #     chat_model_cls = SoopChatEntry
        else:
            # 기본 모델 혹은 에러 처리
            logger.warning(f"Unknown platform code: {platform_code}. Using default ChatEntry.")
            chat_model_cls = ChatEntry

        # 2. Chat Logs 스트림 준비
        chat_key = StoragePaths.get_chat_key(vod_id)
        try:
            raw_chat_stream = self.tmp_storage.read_jsonl_stream(chat_key)

            # [핵심] 결정된 플랫폼 전용 모델 클래스를 주입
            model_chat_stream = self.context_assembler.as_model_stream(stream=raw_chat_stream, model=chat_model_cls)
            iterators.append(model_chat_stream)
        except FileNotFoundError:
            logger.warning(f"Chat log not found for VOD {vod_id}")

        # 3. ASR Logs 스트림 준비 (플랫폼 공통 가정)
        asr_key = StoragePaths.get_asr_key(vod_id)
        try:
            raw_asr_stream = self.tmp_storage.read_jsonl_stream(asr_key)

            model_asr_stream = self.context_assembler.as_model_stream(stream=raw_asr_stream, model=ASREntry)
            iterators.append(model_asr_stream)
        except FileNotFoundError:
            logger.warning(f"ASR log not found for VOD {vod_id}")

        if not iterators:
            raise FileNotFoundError(f"No valid log sources found for VOD {vod_id}")

        return iterators

    async def generate_segment_summaries(self, platform: PlatformCode, channel_id: int, vod_id: int):
        logger.info(f"Starting segment summary generation for VOD: {vod_id}")

        start_at = self._get_utc_now()
        step_status = VODPipelineStepStatus.FAILED
        pipeline_step = VODProcessingStep.GENERATE_SEGMENT_SUMMARY
        segment_summary_key = StoragePaths.get_segment_summary_key(vod_id)

        if await self._is_step_completed(vod_id, pipeline_step):
            return segment_summary_key

        try:
            # 1. Prompt Path 확인
            llm_task = LLMTask.SEGMENT_SUMMARIZE
            prompt_path = self.prompt_paths.get(llm_task)
            if not prompt_path:
                raise ValueError(f"Prompt path not found for task: {llm_task}")

            # 2. Resume 상태 복원
            last_entry = await self._recover_last_segment_summary(vod_id)

            # 윈도우 크기 캐싱 (반복 사용)
            window_size = self.window_config.segment_size

            if last_entry:
                next_valid_start_time = last_entry.timestamp + window_size
                previous_summary = last_entry.content
                logger.info(f"Resuming generation. Next valid window starts at or after: {next_valid_start_time}")
            else:
                next_valid_start_time = 0
                previous_summary = ""

            # 3. 데이터 준비
            platform_metadata_context, channel_metadata_context = await self._fetch_metadata_context(
                platform, channel_id
            )
            log_iterators = await self._create_log_stream_iterators(vod_id, platform)

            # 4. 윈도우 순회 (Main Loop)
            async for window_entries in self.context_assembler.get_windows(
                iterators=log_iterators,
                window_size_ms=window_size,
            ):
                if not window_entries:
                    continue

                # [Step 1] 현재 데이터의 정확한 격자 시간 계산 (Alignment)
                # 예: 10분 01초 데이터 -> 10분 00초 윈도우로 보정
                first_log_ts = window_entries[0].timestamp
                aligned_window_start = (first_log_ts // window_size) * window_size

                # [Step 2] 이미 처리된 구간 Skip
                if aligned_window_start < next_valid_start_time:
                    continue

                # [Step 3] 데이터 공백(Gap) 채우기 (핵심 로직)
                # 스트림이 건너뛴 구간(5분)이 있다면 여기서 강제로 채워 넣습니다.
                while next_valid_start_time < aligned_window_start:
                    logger.info(f"Detected gap. Filling empty entry at {next_valid_start_time}")

                    empty_entry = self._create_empty_segment_summary_entry(next_valid_start_time)
                    await self.tmp_storage.append_jsonl(segment_summary_key, empty_entry.model_dump())

                    # 빈 엔트리라도 컨텍스트는 이어져야 함
                    previous_summary = empty_entry.content
                    next_valid_start_time += window_size

                # [Step 4] 현재 윈도우 처리
                # 정상적인 데이터가 있는 구간 처리
                new_entry = await self._process_segment_window(
                    window_entries=window_entries,
                    current_timestamp=aligned_window_start,  # 보정된 시간 사용
                    platform_metadata_context=platform_metadata_context,
                    channel_metadata_context=channel_metadata_context,
                    previous_summary=previous_summary,
                    prompt_path=prompt_path,
                    output_key=segment_summary_key,
                )

                if new_entry:
                    previous_summary = new_entry.content
                    next_valid_start_time = new_entry.timestamp + window_size

            step_status = VODPipelineStepStatus.COMPLETED
            return segment_summary_key
        except Exception as e:
            logger.error(f"❌ Failed to generate segment summaries for vod_id={vod_id}: {e}")
            await self._fail_pipeline(vod_id)
            raise
        finally:
            await self._record_step_status(vod_id, pipeline_step, step_status, start_at, self._get_utc_now())

    async def _process_segment_window(
        self,
        window_entries: list[BaseStreamEntry],
        current_timestamp: int,
        platform_metadata_context: PlatformMetadataContext,
        channel_metadata_context: ChannelMetadataContext,
        previous_summary: str,
        prompt_path: str,
        output_key: str,
    ) -> SegmentSummaryEntry | None:
        """
        단일 윈도우 처리: 텍스트 변환 -> (빈 경우 Empty 생성) OR (내용 있으면 LLM 호출) -> 저장
        """
        # 1. 텍스트 변환
        broadcast_logs_text = self.context_assembler.format_segment_window_to_text(window_entries)

        # 2. 로그가 없는 경우 (Empty Data Handling)
        # 윈도우는 열렸으나 내용이 비어있는 경우입니다.
        if not broadcast_logs_text:
            empty_entry = self._create_empty_segment_summary_entry(current_timestamp)
            await self.tmp_storage.append_jsonl(output_key, empty_entry.model_dump())
            return empty_entry

        # 3. Input Model 조립
        input_vars = SegmentSummaryGenerationInput.assemble(
            platform_metadata_context=platform_metadata_context,
            channel_metadata_context=channel_metadata_context,
            previous_summary=previous_summary,
            broadcast_logs=broadcast_logs_text,
        )

        # 4. 프롬프트 및 LLM 요청
        messages = self.prompt_manager.build_prompt(prompt_path=prompt_path, variables=input_vars)

        llm_output = await self.llm_client.request_completion(
            messages=messages, model=LLMTask.SEGMENT_SUMMARIZE, response_model=SegmentSummaryGenerationOutput
        )

        # 5. 결과 엔트리 생성 (duration 제거됨)
        new_entry = SegmentSummaryEntry.from_generation_output(
            generation_output=llm_output, timestamp=current_timestamp
        )

        # 6. 저장
        await self.tmp_storage.append_jsonl(output_key, new_entry.model_dump())

        return new_entry

    def _create_empty_segment_summary_entry(self, timestamp: int) -> SegmentSummaryEntry:
        """
        데이터 부족 시 사용할 기본값 엔트리 생성
        """
        empty_output = SegmentSummaryGenerationOutput(
            summary_text="방송 내용이나 채팅 기록이 충분하지 않아 요약할 수 없습니다.",
            atmosphere=StreamAtmosphere.NEUTRAL,
            scores=EvaluationScores(expressiveness=1, reaction_unity=1, significance=1),
            top_keywords=[],
        )

        # duration 제거됨
        return SegmentSummaryEntry.from_generation_output(generation_output=empty_output, timestamp=timestamp)

    async def generate_chapter_summaries(self, platform: PlatformCode, channel_id: int, vod_id: int) -> str:
        start_at = self._get_utc_now()
        step_status = VODPipelineStepStatus.FAILED
        pipeline_step = VODProcessingStep.GENERATE_CHAPTER_SUMMARY
        chapter_summary_key = StoragePaths.get_chapter_summary_key(vod_id)

        if await self._is_step_completed(vod_id, pipeline_step):
            return chapter_summary_key

        logger.info(f"Starting chapter summary generation for VOD: {vod_id}")

        try:
            # 1. Prompt Path 확인
            llm_task = LLMTask.CHAPTER_SUMMARIZE
            prompt_path = self.prompt_paths.get(llm_task)
            if not prompt_path:
                raise ValueError(f"Prompt path not found for task: {llm_task}")

            # 2. Resume 상태 복원
            last_entry = await self._recover_last_chapter_summary(vod_id)

            window_size = self.window_config.chapter_size

            if last_entry:
                next_valid_start_time = last_entry.timestamp + window_size
                logger.info(
                    f"Resuming chapter generation. Next valid window starts at or after: {next_valid_start_time}"
                )
            else:
                next_valid_start_time = 0

            # 3. 데이터 준비
            platform_metadata_context, channel_metadata_context = await self._fetch_metadata_context(
                platform, channel_id
            )

            # [중요] 세그먼트 요약 스트림 생성 (Source)
            summary_iterators = await self._create_summary_stream_iterators(vod_id)

            # 4. 윈도우 순회 (Main Loop)
            async for window_entries in self.context_assembler.get_windows(
                iterators=summary_iterators,
                window_size_ms=window_size,
            ):
                if not window_entries:
                    continue

                # [Step 1] 윈도우 정렬 (Alignment)
                first_entry_ts = window_entries[0].timestamp
                aligned_window_start = (first_entry_ts // window_size) * window_size

                # [Step 2] Skip Check
                if aligned_window_start < next_valid_start_time:
                    continue

                # [Step 3] Gap Filling (방어 로직)
                # Segment Summary가 완벽하다면 실행될 일은 없으나, 데이터 무결성을 위해 유지
                while next_valid_start_time < aligned_window_start:
                    logger.warning(f"Detected gap in chapter stream. Filling empty entry at {next_valid_start_time}")
                    empty_entry = self._create_empty_chapter_summary_entry(next_valid_start_time)
                    await self.tmp_storage.append_jsonl(chapter_summary_key, empty_entry.model_dump())

                    next_valid_start_time += window_size

                # [Step 4] 현재 윈도우 처리
                new_entry = await self._process_chapter_window(
                    window_entries=window_entries,  # List[SegmentSummaryEntry]
                    current_timestamp=aligned_window_start,
                    platform_metadata_context=platform_metadata_context,
                    channel_metadata_context=channel_metadata_context,
                    prompt_path=prompt_path,
                    output_key=chapter_summary_key,
                )

                if new_entry:
                    next_valid_start_time = new_entry.timestamp + window_size

            step_status = VODPipelineStepStatus.COMPLETED

            return chapter_summary_key
        except Exception as e:
            logger.error(f"❌ Failed to generate chapter summaries for vod_id={vod_id}: {e}")
            await self._fail_pipeline(vod_id)
            raise
        finally:
            await self._record_step_status(vod_id, pipeline_step, step_status, start_at, self._get_utc_now())

    # =========================================================================
    # Internal Logic: Chapter Processing
    # =========================================================================

    async def _process_chapter_window(
        self,
        window_entries: list[BaseStreamEntry],  # 실제로는 List[SegmentSummaryEntry]
        current_timestamp: int,
        platform_metadata_context: PlatformMetadataContext,
        channel_metadata_context: ChannelMetadataContext,
        prompt_path: str,
        output_key: str,
    ) -> ChapterSummaryEntry | None:
        """
        여러 개의 세그먼트 요약을 모아 하나의 챕터 요약을 생성합니다.
        """
        # 1. 텍스트 변환
        # ContextAssembler가 SegmentSummaryEntry 리스트를 적절한 텍스트(시간대별 나열 등)로 변환한다고 가정
        segment_summaries_text = self.context_assembler.format_chapter_window_to_text(window_entries)

        # 2. 내용 부족 처리
        if not segment_summaries_text:
            empty_entry = self._create_empty_chapter_summary_entry(current_timestamp)
            await self.tmp_storage.append_jsonl(output_key, empty_entry.model_dump())
            return empty_entry

        # 3. Input Model 조립
        # ChapterSummaryGenerationInput은 broadcast_logs 대신 segment_summaries를 필드로 가질 것입니다.
        input_vars = ChapterSummaryGenerationInput.assemble(
            platform_metadata_context=platform_metadata_context,
            channel_metadata_context=channel_metadata_context,
            segment_summaries=segment_summaries_text,  # 세그먼트 요약들의 모음
        )

        # 4. 프롬프트 및 LLM 요청
        messages = self.prompt_manager.build_prompt(prompt_path=prompt_path, variables=input_vars)

        llm_output = await self.llm_client.request_completion(
            messages=messages, model=LLMTask.CHAPTER_SUMMARIZE, response_model=ChapterSummaryGenerationOutput
        )

        # 5. 결과 엔트리 생성
        new_entry = ChapterSummaryEntry.from_generation_output(
            generation_output=llm_output, timestamp=current_timestamp
        )

        # 6. 저장
        await self.tmp_storage.append_jsonl(output_key, new_entry.model_dump())

        return new_entry

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _recover_last_chapter_summary(self, vod_id: int) -> ChapterSummaryEntry | None:
        """저장된 챕터 요약 파일의 마지막 엔트리를 복원합니다."""
        chapter_summary_key = StoragePaths.get_chapter_summary_key(vod_id)

        try:
            entries = await self.tmp_storage.read_jsonl(chapter_summary_key)
        except FileNotFoundError:
            return None

        if entries:
            last_data = entries[-1]
            return ChapterSummaryEntry.model_validate(last_data)

        return None

    def _create_empty_chapter_summary_entry(self, timestamp: int) -> ChapterSummaryEntry:
        """데이터 부족 시 사용할 기본 챕터 엔트리"""
        empty_output = ChapterSummaryGenerationOutput.model_validate({"title": "요약 정보 없음", "key_topics": []})

        return ChapterSummaryEntry.from_generation_output(generation_output=empty_output, timestamp=timestamp)

    async def _create_summary_stream_iterators(self, vod_id) -> list[AsyncIterable[BaseStreamEntry]]:
        iterators: list[AsyncIterable[BaseStreamEntry]] = []

        # 1. 파일 경로 키 획득
        segment_summary_key = StoragePaths.get_segment_summary_key(vod_id)

        try:
            # 2. Raw Stream 획득
            raw_summary_stream = self.tmp_storage.read_jsonl_stream(segment_summary_key)

            # 3. Model Stream 변환 (SegmentSummaryEntry)
            # SegmentSummaryEntry는 BaseStreamEntry(timestamp 포함)와 호환되어야 합니다.
            model_summary_stream = self.context_assembler.as_model_stream(
                stream=raw_summary_stream, model=SegmentSummaryEntry
            )
            iterators.append(model_summary_stream)

        except FileNotFoundError:
            # Chapter Summary는 Segment Summary가 없으면 수행할 수 없으므로 에러 처리
            logger.error(f"Segment summaries source file not found for VOD {vod_id}")
            raise

        return iterators
