from collections.abc import AsyncIterable

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.pipeline.implementations.base import BasePipelineService
from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_core.constants.service_codes import FileKeyTemplate, PlatformCode
from chatzzk_core.schemas.external.chzzk import ChzzkVideoChat
from chatzzk_core.schemas.internal.models import ChzzkChatEntry
from chatzzk_data_access.repositories.vod import VODRepository
from chatzzk_data_access.storages.local_storage import LocalStorage


class ChzzkChatCollectionService(BasePipelineService):
    def __init__(
        self,
        chzzk_api_client: ChzzkAPIClient,
        vod_repo: VODRepository,
        tmp_storage: LocalStorage,
        db_session_factory: async_sessionmaker[AsyncSession],
    ):
        self.chzzk_api_client = chzzk_api_client
        self.vod_repo = vod_repo
        self.tmp_storage = tmp_storage
        self.db_session_factory = db_session_factory
        self.platform_code = PlatformCode.CHZZK

    async def _async_chat_stream_generator(
        self, async_logs_iterable: AsyncIterable[list[ChzzkVideoChat]]
    ) -> AsyncIterable[dict]:
        async for batch in async_logs_iterable:
            for log in batch:
                yield ChzzkChatEntry.from_video_chat(log).model_dump()

    async def collect_and_save_chats(self, video_no: str, duration: int) -> str:
        """
        [Action] 실제 채팅 수집 및 파일 저장 수행
        Return:
            str: 저장된 파일 경로
        """
        try:
            chat_key = FileKeyTemplate.get_chat_key(self.platform_code, video_no)
            vod_chat_agen = self.chzzk_api_client.fetch_video_chats(video_no, duration)
            vod_chat_mapped_agen = self._async_chat_stream_generator(vod_chat_agen)

            # Assuming write_jsonl_stream returns the number of lines written
            chat_key = await self.tmp_storage.write_jsonl_stream(chat_key, vod_chat_mapped_agen)

            return chat_key
        except Exception as e:
            logger.error(f"❌ Failed to collect and save chats for video_no {video_no}: {e}")
            raise
