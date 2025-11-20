import aiohttp
from dependency_injector import containers, providers

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_clients.media.media_processor import MediaProcessor
from chatzzk_clients.ml.asr.factory import create_asr_client
from chatzzk_clients.ml.vad.factory import create_vad_client
from chatzzk_schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk_schemas.config.clients.http import AioHTTPConfig
from chatzzk_schemas.config.clients.media_processor import MediaProcessorConfig
from chatzzk_schemas.config.clients.ml import (
    validate_asr_config,
    validate_vad_config,
)


async def init_client_session():  # https://python-dependency-injector.ets-labs.org/providers/async.html 이를 의존하는 provider 역시 await으로 호출
    session = aiohttp.ClientSession()
    yield session


class ClientContainer(containers.DeclarativeContainer):
    """clients 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Configuration()

    _session = providers.Resource(init_client_session)

    _aiohttp_config = providers.Callable(
        AioHTTPConfig.model_validate,
        config.aiohttp,
    )

    _chzzk_api_config = providers.Callable(
        ChzzkAPIConfig.model_validate,
        config.chzzk_api,
    )

    _media_processor_config = providers.Callable(
        MediaProcessorConfig.model_validate,
        config.media_processor,
    )

    _vad_config = providers.Callable(validate_vad_config, config.vad)

    _asr_config = providers.Callable(validate_asr_config, config.asr)

    # 중첩된 pydantic model을 위처럼 따로 정의를 해줘야하고 callable로 정의하여 아래 factory에서 호출할 때 call하므로 인스턴스로 주입됨
    aiohttp_client = providers.ThreadSafeSingleton(AioHTTPClient, config=_aiohttp_config, session=_session)

    chzzk_api_client = providers.ThreadSafeSingleton(
        ChzzkAPIClient,
        config=_chzzk_api_config,
        http_client=aiohttp_client,
    )

    media_processor = providers.ThreadSafeSingleton(
        MediaProcessor,
        config=_media_processor_config,
        http_client=aiohttp_client,
    )

    vad_client_factory = providers.ThreadSafeSingleton(create_vad_client, model_config=_vad_config)

    asr_client_factory = providers.ThreadSafeSingleton(
        create_asr_client, model_config=_asr_config, http_client=aiohttp_client
    )
