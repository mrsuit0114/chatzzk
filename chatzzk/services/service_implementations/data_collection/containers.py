from dependency_injector import containers, providers

from chatzzk_constants.service_codes import PlatformCode
from chatzzk.services.service_implementations.data_collection.chzzk_data_collection import ChzzkDataCollectionService


class DataCollectionContainer(containers.DeclarativeContainer):
    db_session_factory = providers.Dependency()
    vod_repo = providers.Dependency()
    tmp_storage = providers.Dependency()
    chzzk_api_client = providers.Dependency()
    media_processor = providers.Dependency()

    _chzzk_data_collection_service = providers.Factory(
        ChzzkDataCollectionService,
        db_session_factory=db_session_factory,
        vod_repo=vod_repo,
        tmp_storage=tmp_storage,
        media_processor=media_processor,
        chzzk_api_client=chzzk_api_client,
    )

    data_collection_factory = providers.Aggregate({PlatformCode.CHZZK: _chzzk_data_collection_service})
