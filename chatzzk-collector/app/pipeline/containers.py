from dependency_injector import containers, providers

from app.pipeline.di_containers.client_containers import ClientContainer
from app.pipeline.di_containers.data_access_containers import DataAccessContainer
from app.pipeline.implementations.asr_service import ASRService
from app.pipeline.implementations.audio_discovery_services import ChzzkAudioCollectionService
from app.pipeline.implementations.chat_collection_services import ChzzkChatCollectionService
from app.pipeline.implementations.vad_service import VADService
from app.pipeline.implementations.vod_discovery_services import ChzzkVODDiscoveryService
from chatzzk_core.constants.service_codes import PlatformCode
from chatzzk_core.schemas.config.services.vod_discovery import ChzzkVODFilterConfig
from chatzzk_core.schemas.config.settings import Settings


class AppContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    clients_package = providers.Container(
        ClientContainer,
        config=settings.provided.clients,
    )

    data_access_package = providers.Container(
        DataAccessContainer,
        config=settings.provided.data_access,
    )

    _chzzk_vod_discovery_service = providers.Singleton(
        ChzzkVODDiscoveryService,
        channel_repo=data_access_package.channel_repo,
        vod_repo=data_access_package.vod_repo,
        chzzk_api_client=clients_package.chzzk_api_client,
        db_session_factory=data_access_package.db_session_factory,
        filter_config=ChzzkVODFilterConfig(),
    )

    _chzzk_chat_collection_service = providers.Singleton(
        ChzzkChatCollectionService,
        chzzk_api_client=clients_package.chzzk_api_client,
        vod_repo=data_access_package.vod_repo,
        tmp_storage=data_access_package.tmp_storage,
        db_session_factory=data_access_package.db_session_factory,
    )

    _chzzk_audio_collection_service = providers.Singleton(
        ChzzkAudioCollectionService,
        chzzk_api_client=clients_package.chzzk_api_client,
        vod_repo=data_access_package.vod_repo,
        tmp_storage=data_access_package.tmp_storage,
        db_session_factory=data_access_package.db_session_factory,
        media_processor=clients_package.media_processor,
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
        audio_loader=clients_package.audio_loader,
        vod_repo=data_access_package.vod_repo,
        vad_client=clients_package.vad_client_factory,
        tmp_storage=data_access_package.tmp_storage,
        db_session_factory=data_access_package.db_session_factory,
    )

    asr_service = providers.Singleton(
        ASRService,
        audio_loader=clients_package.audio_loader,
        vod_repo=data_access_package.vod_repo,
        asr_client=clients_package.asr_client_factory,
        tmp_storage=data_access_package.tmp_storage,
        db_session_factory=data_access_package.db_session_factory,
    )
