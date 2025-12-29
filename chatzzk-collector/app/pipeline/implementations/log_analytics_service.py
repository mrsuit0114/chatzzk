from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from app.schemas.dashboard import (
    ChapterItem,
    DashboardMetaInfo,
    DashboardResponse,
    DashboardStats,
    SegmentItem,
    StatSeries,
    StreamLogItem,
    StreamLogResponse,
)
from chatzzk_clients.analytics import StreamStatsCalculator
from chatzzk_clients.llm import ContextAssembler
from chatzzk_core.constants import (
    EntryTypeCode,
    PlatformCode,
    StoragePaths,
    StreamWindowConstant,
    VODPipelineStepStatus,
    VODProcessingStep,
)
from chatzzk_core.schemas.internal import ASREntry, ChapterSummaryDict, ChatEntry, SegmentSummaryDict, StreamEntryDict
from chatzzk_data_access.repositories import VODRepository
from chatzzk_data_access.storages import LocalStorage


class LogAnalyticsService(BasePipelineService):
    def __init__(
        self,
        vod_repo: VODRepository,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
        stream_stats_calculator: StreamStatsCalculator,
        context_assembler: ContextAssembler,
    ):
        super().__init__(vod_repo, db_session_factory)
        self.tmp_storage = tmp_storage
        self.calculator = stream_stats_calculator
        self.context_assembler = context_assembler

    async def _load_logs(
        self, vod_id: int
    ) -> tuple[list[StreamEntryDict], list[SegmentSummaryDict], list[ChapterSummaryDict], list[StreamEntryDict]]:
        chat_key = StoragePaths.get_chat_key(vod_id)
        segment_summary_key = StoragePaths.get_segment_summary_key(vod_id)
        chapter_summary_key = StoragePaths.get_chapter_summary_key(vod_id)

        chat_stream = self.tmp_storage.read_jsonl_stream(chat_key)
        segment_summary_stream = self.tmp_storage.read_jsonl_stream(segment_summary_key)
        chapter_summary_stream = self.tmp_storage.read_jsonl_stream(chapter_summary_key)

        chat_entries = [entry async for entry in chat_stream]
        segment_summary_entries = [entry async for entry in segment_summary_stream]
        chapter_summary_entries = [entry async for entry in chapter_summary_stream]

        return chat_entries, segment_summary_entries, chapter_summary_entries

    def _construct_response(
        self,
        platform: PlatformCode,
        vod: dict,
        stats_clip: dict[str, int],
        stats_seg: dict[str, int],
        atmo: dict[str, int],
        segments: list[SegmentSummaryDict],
        chapters: list[ChapterSummaryDict],
    ) -> DashboardResponse:
        """
        [Mapper 메서드]
        흩어져 있는 데이터를 모아 DashboardResponse 스키마로 조립합니다.
        """

        # 1. 메타 정보 조립
        meta_info = DashboardMetaInfo(
            platform=platform,
            title=vod["video_title"],
            channel_id=vod["platform_channel_id"],
            channel_name=vod["channel_name"],
            video_no=vod["video_no"],
            publish_date=vod["publish_date"],
            duration=vod["duration"],
        )

        # 2. 통계 정보 조립 (StatSeries 재사용)
        stats = DashboardStats(
            clip=StatSeries(volume=stats_clip["volume"], momentum=stats_clip["momentum"]),
            segment=StatSeries(volume=stats_seg["volume"], momentum=stats_seg["momentum"]),
            atmosphere=atmo,
        )

        # 3. 리스트 데이터 매핑 (List Comprehension 활용)
        # Raw Dict -> Schema Model 변환
        segment_items = []
        for seg in segments:
            raw_scores = seg.get("scores", {})

            avg_score = self.calculator.calculate_avg_score(raw_scores)

            item = SegmentItem(
                txt=seg["content"],
                kwd=seg.get("keywords", []),
                sc=avg_score,
                atmo=seg.get("atmosphere", "중립"),
                vol_peak=seg.get("vol_peak", {}),
                mmt_peak=seg.get("mmt_peak", {}),
            )
            segment_items.append(item)

        chapter_items = [ChapterItem(title=chap["title"], txt=chap["content"]) for chap in chapters]

        # 4. 최종 Root 모델 반환
        return DashboardResponse(
            # version 필드는 모델 내부 기본값("1.0") 사용
            meta_info=meta_info,
            stats=stats,
            segments=segment_items,
            chapters=chapter_items,
        )

    async def _process_analytics(self, vod_id: int, platform: PlatformCode) -> str:
        # 분석하고 웹 서비스에서 사용할 구조로 가공해서 저장
        analytics_key = StoragePaths.get_analytics_key(vod_id)
        chat_entries, segment_summary_entries, chapter_summary_entries = await self._load_logs(vod_id)

        async with self.db_session_factory() as session:
            vod = await self.vod_repo.get_vod_with_channel(session, vod_id)
            vod_dict = {
                "video_title": vod.video_title,
                "platform_channel_id": vod.channel.platform_channel_id,
                "channel_name": vod.channel.channel_name,
                "video_no": vod.video_no,
                "publish_date": vod.publish_date,
                "duration": vod.duration,
            }

        clip_step = StreamWindowConstant.CLIP_SIZE
        seg_step = StreamWindowConstant.SEGMENT_SIZE

        duration_offseted = vod_dict["duration"] + 1

        stats_clip_raw = self.calculator.calculate_stream_metrics(chat_entries, duration_offseted, clip_step, sigma=1.0)
        stats_seg_raw = self.calculator.calculate_stream_metrics(chat_entries, duration_offseted, seg_step, sigma=1.0)
        atmo_raw = self.calculator.calculate_atmosphere_ratio(segment_summary_entries)

        self.calculator.attach_peaks_to_segments(
            segments=segment_summary_entries,
            clip_stats=stats_clip_raw,
            clip_window_ms=clip_step,
            segment_window_ms=seg_step,
        )

        dashboard_payload = self._construct_response(
            platform,
            vod_dict,
            stats_clip_raw,
            stats_seg_raw,
            atmo_raw,
            segment_summary_entries,
            chapter_summary_entries,
        )

        await self.tmp_storage.write_json(analytics_key, dashboard_payload.model_dump(by_alias=True))

        return analytics_key

    async def _generate_stream_logs(self, vod_id: int) -> str:
        # asr_entries.jsonl과 chat_entries.jsonl을 읽어 context_assembler로부터 padding 적용, preprocess_chat을 false로 설정한 window를 duration//ChapterSize만큼 생성

        asr_key = StoragePaths.get_asr_key(vod_id)
        chat_key = StoragePaths.get_chat_key(vod_id)

        asr_stream = self.tmp_storage.read_jsonl_stream(asr_key)
        chat_stream = self.tmp_storage.read_jsonl_stream(chat_key)

        asr_model_stream = self.context_assembler.as_model_stream(asr_stream, ASREntry)
        chat_model_stream = self.context_assembler.as_model_stream(chat_stream, ChatEntry)

        stream_logs_index = 0
        async for window_entries in self.context_assembler.get_windows(
            iterators=[asr_model_stream, chat_model_stream],
            window_size_ms=StreamWindowConstant.CHAPTER_SIZE,
            padding_ms=StreamWindowConstant.STREAM_LOG_PADDING_SIZE,
            preprocess_chat=False,
        ):
            stream_logs_key = StoragePaths.get_stream_logs_key(vod_id, stream_logs_index)
            stream_logs = []
            for entry in window_entries:
                stream_log = StreamLogItem(
                    ts=entry.timestamp,
                    ty=EntryTypeCode.from_entry_type(entry.entry_type),
                    u=getattr(entry, "nickname", None),
                    c=entry.content,
                )
                stream_logs.append(stream_log)
            stream_log = StreamLogResponse(stream_logs=stream_logs)
            await self.tmp_storage.write_json(stream_logs_key, stream_log.model_dump(exclude_none=True, by_alias=True))
            stream_logs_index += 1

        return stream_logs_key

    async def process(self, vod_id: int, platform: PlatformCode) -> str:
        start_at = self._get_utc_now()
        analytics_key = StoragePaths.get_analytics_key(vod_id)
        step_status = VODPipelineStepStatus.FAILED
        pipeline_step = VODProcessingStep.GENERATE_ANALYTICS
        if await self._is_step_completed(vod_id, pipeline_step):
            return analytics_key

        try:
            analytics_key = await self._process_analytics(vod_id, platform)
            await self._generate_stream_logs(vod_id)
            step_status = VODPipelineStepStatus.COMPLETED
        except Exception as e:
            logger.error(f"[Process Analytics Error] VOD {vod_id} failed: {str(e)}")
            await self._fail_pipeline(vod_id)
            raise
        finally:
            await self._record_step_status(vod_id, pipeline_step, step_status, start_at, self._get_utc_now())

        return analytics_key
