from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_clients.ml.vad import VADClientInterface
from chatzzk_core.constants import StoragePaths
from chatzzk_data_access.repositories import VODRepository
from chatzzk_data_access.storages import LocalStorage


class VADService(BasePipelineService):
    def __init__(
        self,
        audio_loader: AudioLoader,
        vod_repo: VODRepository,
        vad_client: VADClientInterface,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(vod_repo, db_session_factory)
        self.audio_loader = audio_loader
        self.vad_client = vad_client
        self.tmp_storage = tmp_storage

    async def perform_vad(self, vod_id: int) -> str:
        audio_key = StoragePaths.get_audio_key(vod_id=vod_id)
        vad_timestamps_key = StoragePaths.get_vad_timestamps_key(vod_id=vod_id)

        try:
            audio_path = self.tmp_storage.get_absolute_path(audio_key)
            audio_np, _ = self.audio_loader.load(audio_path)

            speech_timestamps = await self.vad_client.detect_speech(audio_np)
            vad_key = await self.tmp_storage.write_jsonl(vad_timestamps_key, speech_timestamps)

            return vad_key

        except Exception as e:
            logger.error(f"Failed to perform VAD for vod_id={vod_id}: {e}")
            raise
