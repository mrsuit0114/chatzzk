import aiohttp
from dependency_injector import containers, providers

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_clients.chzzk.chzzk_api_client import ChzzkAPIClient
from chatzzk_clients.media.media_processor import MediaProcessor
from chatzzk_clients.ml.asr.factory import create_asr_client
from chatzzk_clients.ml.vad.factory import create_vad_client
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_clients.llm.prompt_builder import PromptBuilder
from chatzzk_clients.llm.litellm_proxy_client import LiteLLMProxyClient
from chatzzk_schemas.config.clients.chzzk import ChzzkAPIConfig
from chatzzk_schemas.config.clients.http import AioHTTPConfig
from chatzzk_schemas.config.clients.media_processor import MediaProcessorConfig
from chatzzk_schemas.config.clients.ml import (
    validate_asr_config,
    validate_vad_config,
    AudioLoaderConfig,
)
from chatzzk_schemas.config.clients.llm import LangfuseConfig, LiteLLMProxyConfig


async def init_client_session():  # https://python-dependency-injector.ets-labs.org/providers/async.html 이를 의존하는 provider 역시 await으로 호출
    session = aiohttp.ClientSession()
    yield session


class ClientContainer(containers.DeclarativeContainer):
    """clients 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Configuration()

    _session = providers.Resource(init_client_session)

    _audio_loader_config = providers.Callable(
        AudioLoaderConfig.model_validate,
        config.audio_loader,
    )

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
    _prompt_builder_config = providers.Callable(
        LangfuseConfig.model_validate,
        config.prompt_builder,
    )
    _llm_client_config = providers.Callable(
        LiteLLMProxyConfig.model_validate,
        config.llm_proxy,
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

    audio_loader = providers.Factory(AudioLoader, config=_audio_loader_config)

    vad_client_factory = providers.Singleton(create_vad_client, model_config=_vad_config)

    asr_client_factory = providers.Singleton(create_asr_client, model_config=_asr_config, http_client=aiohttp_client)

    prompt_builder = providers.Singleton(
        PromptBuilder,
        config=_prompt_builder_config,
    )

    llm_client = providers.Singleton(
        LiteLLMProxyClient,
        config=_llm_client_config,
        session=_session,
    )
