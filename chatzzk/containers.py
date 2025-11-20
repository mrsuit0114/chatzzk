from dependency_injector import containers, providers

from chatzzk.services.service_implementations.di_containers.client_containers import ClientContainer
from chatzzk.services.service_implementations.di_containers.data_access_containers import DataAccessContainer
from chatzzk.services.service_implementations.data_collection.containers import DataCollectionContainer
from chatzzk.services.service_implementations.discovery.conatiners import DiscoveryContainer
from chatzzk.services.service_implementations.management.containers import ManagementContainer
from chatzzk.services.service_implementations.speech_processing.containers import SpeechProcessingContainer


class AppContainer(containers.DeclarativeContainer):
    """
    애플리케이션의 모든 컨테이너를 조립하고 설정을 제공하는 최상위 컨테이너
    하나의 컨테이너에 여러 프로세스에서 싱글톤에 접근하는 상황이 나오나? -> aiohttp 등에 접근할 때 동시에 접근할 가능성이 있음
    """

    config = providers.Configuration()

    data_access_package = providers.Container(DataAccessContainer, config=config.data_access)

    clients_package = providers.Container(
        ClientContainer,
        config=config.clients,
    )

    #
    management_service_package = providers.Container(
        ManagementContainer,
        db_session_factory=data_access_package.db_session_factory,
        platform_repo=data_access_package.platform_repo,
        channel_repo=data_access_package.channel_repo,
        chzzk_api_client=clients_package.chzzk_api_client,
    )

    discovery_service_package = providers.Container(
        DiscoveryContainer,
        config=config.vod_discovery_service,
        db_session_factory=data_access_package.db_session_factory,
        channel_repo=data_access_package.channel_repo,
        vod_repo=data_access_package.vod_repo,
        chzzk_api_client=clients_package.chzzk_api_client,
    )

    # 서비스 패키지 내부에서는 변수에 service를 붙이지 말 것
    data_collection_service_package = providers.Container(
        DataCollectionContainer,
        db_session_factory=data_access_package.db_session_factory,
        tmp_storage=data_access_package.pipeline_storage,
        media_processor=clients_package.media_processor,
        chzzk_api_client=clients_package.chzzk_api_client,
        vod_repo=data_access_package.vod_repo,
    )

    speech_processing_service_package = providers.Container(
        SpeechProcessingContainer,
        tmp_storage=data_access_package.pipeline_storage,
        vod_repo=data_access_package.vod_repo,
        media_processor=clients_package.media_processor,
        db_session_factory=data_access_package.db_session_factory,
        vad_client=clients_package.vad_client_factory,
        asr_client=clients_package.asr_client_factory,
    )
