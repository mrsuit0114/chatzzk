# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# from app.pipeline.implementations.base import BasePipelineService
# from chatzzk_clients.llm import ContextAssembler, LLMClient, PromptManager
# from chatzzk_core.constants import PlatformCode, StoragePaths, StreamContextWindowConfig
# from chatzzk_core.schemas.internal import ASREntry, ChatEntry, ChzzkChatEntry, SegmentSummaryGenerationInput
# from chatzzk_data_access.repositories import ChannelRepository, VODRepository
# from chatzzk_data_access.storages import LocalStorage


# # 각 서비스는 병렬수행이 가능한가?
# class LLMGenerationService(BasePipelineService):
#     def __init__(
#         self,
#         tmp_storage: LocalStorage,
#         channel_repo: ChannelRepository,
#         vod_repo: VODRepository,
#         db_session_factory: async_sessionmaker[AsyncSession],
#         context_assembler: ContextAssembler,
#         prompt_manager: PromptManager,
#         llm_client: LLMClient,
#     ):
#         super().__init__(db_session_factory)
#         self.tmp_storage = tmp_storage
#         self.llm_client = llm_client
#         self.prompt_manager = prompt_manager
#         self.channel_repo = channel_repo
#         self.context_assembler = context_assembler
#         self.prompt_manager = prompt_manager
#         self.llm_client = llm_client
#         self.window_config = StreamContextWindowConfig()

#     async def _get_channel_metadata(self, vod_id: int):
#         channel_id = self.vod_repo

#     async def generate_segment_summaries(self, vod_id: int, platform: PlatformCode):
#         # vod_id로 chat, asr 데이터 스트림 가져오기 - tmp_storage
#         # vod_id로 channel_metadata 가져오기 - db
#         # context_assembler를 사용하여 window로 획득
#         # prompt_manager를 사용하여 prompt 생성
#         # llm_client를 사용하여 summary 생성
#         # summary를 tmp_storage에 저장

#         chat_key = StoragePaths.get_chat_key(vod_id)
#         asr_key = StoragePaths.get_asr_key(vod_id)

#         chat_stream = self.tmp_storage.read_jsonl_stream(chat_key)
#         asr_stream = self.tmp_storage.read_jsonl_stream(asr_key)
#         if platform == PlatformCode.CHZZK:
#             chat_model_stream = self.context_assembler.as_model_stream(chat_stream, ChzzkChatEntry)
#         else:
#             chat_model_stream = self.context_assembler.as_model_stream(chat_stream, ChatEntry)
#         asr_model_stream = self.context_assembler.as_model_stream(asr_stream, ASREntry)

#         async for window_entries in self.context_assembler.get_windows(
#             iterators=[chat_model_stream, asr_model_stream],
#             window_size_ms=self.window_config.SEGMENT,
#         ):
#             broadcast_logs = self.context_assembler.format_window_to_text(window_entries)
#             segment_summary_input = SegmentSummaryGenerationInput(
#                 broadcast_logs=broadcast_logs,
#                 vod_id=vod_id,
#                 platform=platform,
#             )

#             prompt = self.prompt_manager.build_prompt()
#             summary = await self.llm_client.generate_summary(prompt)
#             self.tmp_storage.write_jsonl(StoragePaths.get_summary_key(vod_id), summary)
