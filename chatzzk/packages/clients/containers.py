import aiohttp
from dependency_injector import containers, providers

from chatzzk.packages.clients._http.aiohttp_client import AioHTTPClient
from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk.packages.clients.media.media_processor import MediaProcessor
from chatzzk.packages.schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk.packages.schemas.config.clients.http import AioHTTPConfig
from chatzzk.packages.schemas.config.clients.media_processor import MediaProcessorConfig


async def init_client_session():  # https://python-dependency-injector.ets-labs.org/providers/async.html 이를 의존하는 provider 역시 await으로 호출
    session = aiohttp.ClientSession()
    yield session


class ClientsContainer(containers.DeclarativeContainer):
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

    # 중첩된 pydantic model을 위처럼 따로 정의를 해줘야하고 callable로 정의하여 아래 factory에서 호출할 때 call하므로 인스턴스로 주입됨
    aiohttp_client = providers.Singleton(AioHTTPClient, config=_aiohttp_config, session=_session)

    chzzk_api_client = providers.Singleton(
        ChzzkAPIClient,
        config=_chzzk_api_config,
        http_client=aiohttp_client,
    )

    media_processor = providers.Singleton(
        MediaProcessor,
        config=_media_processor_config,
        http_client=aiohttp_client,
    )
