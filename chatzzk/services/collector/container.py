# chatzzk/services/collector/container.py
from dependency_injector import containers, providers

from chatzzk.packages.data_access.db.factory import create_db_engine, create_db_session_provider
from chatzzk.packages.data_access.repositories.analysis import (
    AnalysisResultRepository,
)
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository
from chatzzk.packages.data_access.storage.factory import create_storage_manager
from chatzzk.packages.ml_clients.asr.factory import create_asr_client
from chatzzk.packages.ml_clients.vad.factory import create_vad_client
from chatzzk.services.collector.platform_client.chzzk.chzzk_platform_client import (
    ChzzkPlatformClient,
)
from chatzzk.services.collector.services.vod_discovery_service import VodDiscoveryService
from chatzzk.services.collector.services.vod_processing_service import VodProcessingService
from chatzzk.services.collector.settings import collector_settings


class Container(containers.DeclarativeContainer):
    """
    프로젝트의 의존성을 관리하는 DI 컨테이너입니다.
    """

    # --- Configuration ---
    # collector_settings 객체를 컨테이너 설정으로 사용
    config = providers.Configuration()
    config.from_pydantic(collector_settings)

    # --- Database ---
    # 1. DB 엔진을 위한 프로바이더를 명시적으로 정의
    db_engine = providers.Singleton(create_db_engine, db_config=providers.Object(collector_settings.db_config))

    # 2. 세션 프로바이더는 위에서 만든 db_engine 프로바이더를 주입받음
    db_session_provider = providers.Singleton(create_db_session_provider, engine=db_engine)

    # --- Repositories ---
    # Repository는 DB 세션에 의존하므로, 사용할 때 세션을 주입받는 팩토리로 정의
    vod_repo = providers.Factory(VodRepository)
    channel_repo = providers.Factory(ChannelRepository)
    analysis_repo = providers.Factory(AnalysisResultRepository)

    # --- Clients & Managers (Singletons) ---
    # 애플리케이션(워커) 수명 동안 단일 인스턴스로 유지
    chzzk_client = providers.Singleton(ChzzkPlatformClient)

    storage_manager = providers.Singleton(
        create_storage_manager,
        storage_config=providers.Object(config.storage_config),
    )

    vad_client = providers.Singleton(
        create_vad_client,
        model_config=providers.Object(config.vad_model_config),
    )

    # processing.py의 기존 로직을 반영하여 models_base_dir을 하드코딩
    asr_client = providers.Singleton(create_asr_client, model_config=providers.Object(config.asr_model_config))

    vod_discovery_service = providers.Factory(
        VodDiscoveryService,
        db_session_provider=db_session_provider,  # DB 세션이 아닌 'Provider'를 주입
        chzzk_client=chzzk_client,
    )

    vod_processing_service = providers.Factory(
        VodProcessingService,
        db_session_provider=db_session_provider,
        chzzk_client=chzzk_client,
        vad_client=vad_client,
        asr_client=asr_client,
        storage_manager=storage_manager,
    )
