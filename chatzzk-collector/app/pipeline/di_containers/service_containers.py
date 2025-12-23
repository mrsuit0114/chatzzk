from dependency_injector import containers, providers

from app.pipeline.implementations.asr_service import ASRService
from app.pipeline.implementations.audio_collection_services import ChzzkAudioCollectionService
from app.pipeline.implementations.chat_collection_services import ChzzkChatCollectionService
from app.pipeline.implementations.vad_service import VADService
from app.pipeline.implementations.vod_discovery_services import ChzzkVODDiscoveryService
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
