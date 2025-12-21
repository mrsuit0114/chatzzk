from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_clients.media.media_processor import MediaProcessor
from chatzzk_core.constants import PlatformCode, StoragePaths
from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.storages.local_storage import LocalStorage


class ChzzkAudioCollectionService(BasePipelineService):
    def __init__(
        self,
        chzzk_api_client: ChzzkAPIClient,
        vod_repo: VODRepository,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
        media_processor: MediaProcessor,
    ):
        super().__init__(vod_repo, db_session_factory)
        self.chzzk_api_client = chzzk_api_client
        self.tmp_storage = tmp_storage
        self.media_processor = media_processor
        self.platform_code = PlatformCode.CHZZK

    async def collect_and_save_audio(self, vod_id: int, video_no: str) -> str:
        """
        [Action] 비디오 정보를 조회하고 조건에 따라 MP4/M3U8 방식으로 오디오(WAV)를 추출하여 저장합니다.

        Args:
            vod_id: DB PK (파일 저장 경로 식별용)
            video_no: Platform ID (API 호출용)

        Returns:
            str: 저장된 오디오 파일의 Key (StoragePaths 기준)
        """
        wav_key = StoragePaths.get_audio_key(vod_id)
        wav_abs_path = self.tmp_storage.get_absolute_path(wav_key)

        # WAV가 저장될 부모 디렉토리 생성
        await self.tmp_storage.ensure_parent_dir(wav_key)

        try:
            # 2. VOD 상세 정보 획득
            vod_info = await self.chzzk_api_client.fetch_vod_info(video_no)

            # 3. in_key 존재 여부에 따른 분기 처리
            if vod_info.in_key:
                # [Case A] MP4 방식 (in_key 존재 시)
                mp4_url = await self.chzzk_api_client.fetch_vod_mp4_url(vod_info.video_id, vod_info.in_key)

                # MediaProcessor 호출 (MP4 -> WAV)
                await self.media_processor.extract_wav_from_mp4_url(mp4_url=mp4_url, output_wav_path=wav_abs_path)

            else:
                # [Case B] M3U8 방식 (in_key 미존재 시)
                m3u8_url = await self.chzzk_api_client.fetch_vod_m3u8_url(vod_info.m3u8_url)

                # 임시 경로 설정
                tmp_dir_key = StoragePaths.get_tmp_dir(vod_id)
                tmp_video_key = StoragePaths.get_tmp_video_key(vod_id)

                tmp_dir_abs = self.tmp_storage.get_absolute_path(tmp_dir_key)
                tmp_video_abs = self.tmp_storage.get_absolute_path(tmp_video_key)

                # 임시 디렉토리(폴더 자체) 생성
                await self.tmp_storage.create_dir(tmp_dir_key)

                # MediaProcessor 호출 (M3U8 Download -> Merge -> Extract -> Cleanup)
                await self.media_processor.download_m3u8_and_extract_wav(
                    m3u8_url=m3u8_url,
                    tmp_dir=str(tmp_dir_abs),
                    video_path=str(tmp_video_abs),
                    output_wav_path=str(wav_abs_path),
                    cleanup=True,
                )

            return wav_key

        except Exception as e:
            logger.error(f"Failed to collect and save audio for video_no {video_no}: {e}")
            raise
