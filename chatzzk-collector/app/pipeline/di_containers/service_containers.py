from dependency_injector import containers, providers

from app.pipeline.implementations.asr_service import ASRService
from app.pipeline.implementations.audio_collection_services import ChzzkAudioCollectionService
from app.pipeline.implementations.chat_collection_services import ChzzkChatCollectionService
from app.pipeline.implementations.llm_generation_service import LLMGenerationService
from app.pipeline.implementations.log_analytics_service import LogAnalyticsService
from app.pipeline.implementations.vad_service import VADService
from app.pipeline.implementations.vod_discovery_services import ChzzkVODDiscoveryService
from app.pipeline.implementations.vod_dispatch_service import VODDispatchService
from app.pipeline.implementations.vod_publishing_service import VODPublishingService
from chatzzk_core.constants import PlatformCode
from chatzzk_core.schemas.config import ServicesConfig


class ServiceContainer(containers.DeclarativeContainer):
    config = providers.Dependency(instance_of=ServicesConfig)
    client = providers.DependenciesContainer()
    data_access = providers.DependenciesContainer()

    _chzzk_vod_discovery_service = providers.Singleton(
        ChzzkVODDiscoveryService,
        channel_repo=data_access.channel_repo,
        vod_repo=data_access.vod_repo,
        chzzk_api_client=client.chzzk_api_client,
        db_session_factory=data_access.db_session_factory,
        config=config.provided.vod_discovery.chzzk,
    )

    _chzzk_chat_collection_service = providers.Singleton(
        ChzzkChatCollectionService,
        chzzk_api_client=client.chzzk_api_client,
        vod_repo=data_access.vod_repo,
        tmp_storage=data_access.tmp_storage,
        db_session_factory=data_access.db_session_factory,
    )

    _chzzk_audio_collection_service = providers.Singleton(
        ChzzkAudioCollectionService,
        chzzk_api_client=client.chzzk_api_client,
        vod_repo=data_access.vod_repo,
        tmp_storage=data_access.tmp_storage,
        db_session_factory=data_access.db_session_factory,
        media_processor=client.media_processor,
    )

    vod_discovery_services = providers.Dict(
        {
            PlatformCode.CHZZK: _chzzk_vod_discovery_service,
        }
    )

    vod_dispatch_service = providers.Singleton(
        VODDispatchService,
        vod_repo=data_access.vod_repo,
        db_session_factory=data_access.db_session_factory,
    )

    chat_collection_services = providers.Dict(
        {
            PlatformCode.CHZZK: _chzzk_chat_collection_service,
        }
    )

    audio_collection_services = providers.Dict(
        {
            PlatformCode.CHZZK: _chzzk_audio_collection_service,
        }
    )

    vad_service = providers.Singleton(
        VADService,
        audio_loader=client.audio_loader,
        vod_repo=data_access.vod_repo,
        vad_client=client.vad_client,
        tmp_storage=data_access.tmp_storage,
        db_session_factory=data_access.db_session_factory,
    )

    asr_service = providers.Singleton(
        ASRService,
        audio_loader=client.audio_loader,
        vod_repo=data_access.vod_repo,
        asr_client=client.asr_client,
        tmp_storage=data_access.tmp_storage,
        db_session_factory=data_access.db_session_factory,
    )

    llm_generation_service = providers.Singleton(
        LLMGenerationService,
        tmp_storage=data_access.tmp_storage,
        platform_repo=data_access.platform_repo,
        channel_repo=data_access.channel_repo,
        vod_repo=data_access.vod_repo,
        db_session_factory=data_access.db_session_factory,
        context_assembler=client.context_assembler,
        llm_client=client.llm_client,
        config=config.provided.llm_generation,
        prompt_manager=client.prompt_manager,
    )

    log_analytics_service = providers.Singleton(
        LogAnalyticsService,
        vod_repo=data_access.vod_repo,
        tmp_storage=data_access.tmp_storage,
        db_session_factory=data_access.db_session_factory,
        stream_stats_calculator=client.stream_stats_calculator,
        context_assembler=client.context_assembler,
    )

    vod_publishing_service = providers.Singleton(
        VODPublishingService,
        vod_repo=data_access.vod_repo,
        db_session_factory=data_access.db_session_factory,
        tmp_storage=data_access.tmp_storage,
        cloud_storage=data_access.cloud_storage,
    )
