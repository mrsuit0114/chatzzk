import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk.packages.clients.media.media_processor import MediaProcessor
from chatzzk.packages.constants.service_codes import (
    FileKeyTemplate,
    PlatformCode,
    VODProcessingStep,
    VODProcessingStepStatus,
)
from chatzzk.packages.data_access.repositories.vod import VODRepository
from chatzzk.packages.data_access.storages.base import PipelineStorage
from chatzzk.packages.schemas.dto.api.chzzk.vod import ChzzkDataCollectRequestDTO, ChzzkDataCollectResponseDTO
from chatzzk.packages.schemas.dto.repo_params.chzzk.vod import ChzzkVODFindParams
from chatzzk.packages.schemas.storage.models import ChzzkChatEntry
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

        tasks = []
        if not chat_done:
            tasks.append((VODProcessingStep.CRAWL_CHATS, self._collect_chats(video_no)))
        if not audio_done:
            tasks.append((VODProcessingStep.DOWNLOAD_AUDIO, self._collect_audio(video_no)))

        results: dict[str, dict[str, Any]] = {}

        if tasks:
            step_names, coros = zip(*tasks, strict=False)
            gather_results = await asyncio.gather(*coros, return_exceptions=True)
            for name, res in zip(step_names, gather_results, strict=False):
                if isinstance(res, Exception):
                    results[name] = {
                        "status": VODProcessingStepStatus.FAILED,
                        "start_time": getattr(res, "start_time", None),
                        "end_time": getattr(res, "end_time", None),
                    }
                else:
                    results[name] = {
                        "status": VODProcessingStepStatus.COMPLETED,
                        "start_time": res["start_time"],
                        "end_time": res["end_time"],
                    }

            async with self.db_session_factory() as session:
                async with session.begin():
                    vod_find_params = ChzzkVODFindParams(video_no=video_no)
                    unified_vod = await self.vod_repo.find_vod_with_platform_vod(
                        session, self.platform_code, vod_find_params
                    )
                    vod = await self.vod_repo.find_vod_with_processing_detail_by_id(session, unified_vod.id)

                    for name, result in results.items():
                        self.vod_repo.update_processing_detail(
                            session,
                            vod,
                            step=name,
                            status=result["status"],
                            start_time=result["start_time"],
                            end_time=result["end_time"],
                        )

        return ChzzkDataCollectResponseDTO(
            video_no=video_no,
            chat_result=results.get(VODProcessingStep.CRAWL_CHATS, {"status": VODProcessingStepStatus.COMPLETED}).get(
                "status"
            ),
            audio_result=results.get(
                VODProcessingStep.DOWNLOAD_AUDIO, {"status": VODProcessingStepStatus.COMPLETED}
            ).get("status"),
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
                    entry = ChzzkChatEntry.from_video_chat(chat)
                    yield entry.model_dump()

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
                self.media_processor.extract_wav_from_mp4_url(mp4_url, output_wav_path)
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
