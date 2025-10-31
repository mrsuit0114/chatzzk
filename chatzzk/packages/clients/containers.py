from dependency_injector import containers, providers

from chatzzk.packages.clients._http.client import BaseHTTPClient
from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk.packages.schemas.config.api import BaseHTTPConfig, ChzzkAPIConfig


class ClientsContainer(containers.DeclarativeContainer):
    """clients 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Configuration()

    _base_http_config = providers.Callable(
        BaseHTTPConfig.model_validate,
        config.base_http,
    )

    _chzzk_api_config = providers.Callable(
        ChzzkAPIConfig.model_validate,
        config.chzzk_api,
    )

    # 중첩된 pydantic model을 위처럼 따로 정의를 해줘야하고 callable로 정의하여 아래 factory에서 호출할 때 call하므로 인스턴스로 주입됨
    # 채팅, discover 등 용도에 따라 구분해서 관리하는게 limiter 관리에 용이할 것
    base_http_client = providers.Factory(
        BaseHTTPClient,
        config=_base_http_config,
    )

    chzzk_api_client = providers.Factory(
        ChzzkAPIClient,
        config=_chzzk_api_config,
        http_client=base_http_client,
    )
