from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from loguru import logger


from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_clients.media.media_processor import MediaProcessor
from chatzzk_constants.service_codes import (
    FileKeyTemplate,
    PlatformCode,
    VODProcessingStep,
    VODProcessingStepStatus,
)
from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.storages.base import PipelineStorage
from chatzzk_schemas.dto.api.chzzk.vod import ChzzkDataCollectRequestDTO, ChzzkDataCollectResponseDTO
from chatzzk_schemas.dto.repo_params.chzzk.vod import ChzzkVODFindParams
from chatzzk.services.interfaces.data_collection import DataCollectionInterface


class ChzzkDataCollectionService(DataCollectionInterface):
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        tmp_storage: PipelineStorage,
        media_processor: MediaProcessor,
        vod_repo: VODRepository,
        chzzk_api_client: ChzzkAPIClient,
    ):
        self.db_session_factory = db_session_factory
        self.chzzk_api_client = chzzk_api_client
        self.tmp_storage = tmp_storage
        self.platform_code = PlatformCode.CHZZK
        self.media_processor = media_processor
        self.vod_repo = vod_repo
        ...

    async def collect_data(self, dto: ChzzkDataCollectRequestDTO) -> ChzzkDataCollectResponseDTO:
        video_no = dto.video_no

        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = ChzzkVODFindParams(video_no=video_no)
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(
                    session, self.platform_code, vod_find_params
                )
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)
                detail = vod.vod_processing_status_detail.status_details or {}

        chat_done = detail.get(VODProcessingStep.CRAWL_CHATS, {}).get("status") == VODProcessingStepStatus.COMPLETED
        audio_done = detail.get(VODProcessingStep.DOWNLOAD_AUDIO, {}).get("status") == VODProcessingStepStatus.COMPLETED

        if chat_done and audio_done:
            return ChzzkDataCollectResponseDTO(
                video_no=video_no,
                chat_result=VODProcessingStepStatus.COMPLETED,
                audio_result=VODProcessingStepStatus.COMPLETED,
            )

        # Sequential execution: Audio first, then Chat
        audio_status = VODProcessingStepStatus.COMPLETED if audio_done else VODProcessingStepStatus.PENDING
        chat_status = VODProcessingStepStatus.COMPLETED if chat_done else VODProcessingStepStatus.PENDING

        if not audio_done:
            try:
                res = await self._collect_audio(video_no)
                await self._update_vod_status(
                    video_no,
                    VODProcessingStep.DOWNLOAD_AUDIO,
                    VODProcessingStepStatus.COMPLETED,
                    res["start_time"],
                    res["end_time"],
                )
                audio_status = VODProcessingStepStatus.COMPLETED
            except Exception as e:
                logger.exception(f"[{VODProcessingStep.DOWNLOAD_AUDIO}] step failed during execution: {e}")
                await self._update_vod_status(
                    video_no,
                    VODProcessingStep.DOWNLOAD_AUDIO,
                    VODProcessingStepStatus.FAILED,
                    getattr(e, "start_time", None),
                    getattr(e, "end_time", None),
                )
                audio_status = VODProcessingStepStatus.FAILED

        if not chat_done:
            try:
                res = await self._collect_chats(video_no)
                await self._update_vod_status(
                    video_no,
                    VODProcessingStep.CRAWL_CHATS,
                    VODProcessingStepStatus.COMPLETED,
                    res["start_time"],
                    res["end_time"],
                )
                chat_status = VODProcessingStepStatus.COMPLETED
            except Exception as e:
                logger.exception(f"[{VODProcessingStep.CRAWL_CHATS}] step failed during execution: {e}")
                await self._update_vod_status(
                    video_no,
                    VODProcessingStep.CRAWL_CHATS,
                    VODProcessingStepStatus.FAILED,
                    getattr(e, "start_time", None),
                    getattr(e, "end_time", None),
                )
                chat_status = VODProcessingStepStatus.FAILED

        return ChzzkDataCollectResponseDTO(
            video_no=video_no,
            chat_result=chat_status,
            audio_result=audio_status,
        )

    async def _update_vod_status(
        self,
        video_no: int,
        step: VODProcessingStep,
        status: VODProcessingStepStatus,
        start_time: datetime | None,
        end_time: datetime | None,
    ):
        async with self.db_session_factory() as session:
            async with session.begin():
                vod_find_params = ChzzkVODFindParams(video_no=video_no)
                unified_vod = await self.vod_repo.find_vod_with_platform_vod(
                    session, self.platform_code, vod_find_params
                )
                vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)

                await self.vod_repo.update_processing_detail(
                    session,
                    vod,
                    step=step,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                )

    async def _collect_chats(self, video_no: int):
        start_time = datetime.now(UTC)
        try:
            async with self.db_session_factory() as session:
                async with session.begin():
                    vod_find_params = ChzzkVODFindParams(video_no=video_no)
                    unified_vod = await self.vod_repo.find_vod_with_platform_vod(
                        session, self.platform_code, vod_find_params
                    )
                    duration_s = unified_vod.chzzk_vod.duration

            video_chats = await self.chzzk_api_client.fetch_vod_chats(video_no, duration_s)

            async def chat_entries_generator():
                for chat in video_chats:
                    entry = chat.to_chat_entry()
                    yield entry.model_dump(exclude_none=True)

            chat_key = FileKeyTemplate.get_chat_key(self.platform_code, video_no)
            await self.tmp_storage.save_jsonl(chat_key, chat_entries_generator())

            return {
                "status": VODProcessingStepStatus.COMPLETED,
                "start_time": start_time,
                "end_time": datetime.now(UTC),
            }

        except Exception as e:
            e.start_time = start_time
            e.end_time = datetime.now(UTC)
            raise e

    async def _collect_audio(self, video_no: int):
        start_time = datetime.now(UTC)
        try:
            vod_info = await self.chzzk_api_client.fetch_vod_info(video_no)
            audio_key = FileKeyTemplate.get_audio_key(self.platform_code, video_no)
            output_wav_path = self.tmp_storage.get_or_create_path(audio_key)

            if vod_info.in_key:
                mp4_url = await self.chzzk_api_client.fetch_vod_mp4_url(vod_info.video_id, vod_info.in_key)
                await self.media_processor.extract_wav_from_mp4_url(mp4_url, output_wav_path)
            else:
                video_key = FileKeyTemplate.get_video_key(self.platform_code, video_no)
                tmp_dir_key = FileKeyTemplate.get_tmp_dir(self.platform_code, video_no)
                video_path = self.tmp_storage.get_or_create_path(video_key)
                tmp_dir_path = self.tmp_storage.get_or_create_path(tmp_dir_key, is_dir=True)
                base_m3u8_url = await self.chzzk_api_client.fetch_vod_m3u8_url(vod_info.m3u8_url)

                await self.media_processor.download_m3u8_and_extract_wav(
                    m3u8_url=base_m3u8_url,
                    tmp_dir=tmp_dir_path,
                    video_path=video_path,
                    output_wav_path=output_wav_path,
                    cleanup=True,
                )

            return {
                "status": VODProcessingStepStatus.COMPLETED,
                "start_time": start_time,
                "end_time": datetime.now(UTC),
            }

        except Exception as e:
            e.start_time = start_time
            e.end_time = datetime.now(UTC)
            raise e
