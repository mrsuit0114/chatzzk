import aiohttp
from dependency_injector import containers, providers
from loguru import logger

from chatzzk_clients._http import AioHTTPClient
from chatzzk_clients.chzzk import ChzzkAPIClient
from chatzzk_clients.llm import ContextAssembler
from chatzzk_clients.media import MediaProcessor
from chatzzk_clients.ml import AudioLoader
from chatzzk_clients.ml.asr import create_asr_client
from chatzzk_clients.ml.vad import create_vad_client
from chatzzk_core.schemas.config import ClientsConfig

# from chatzzk_clients.llm.prompt_builder import PromptBuilder
# from chatzzk_clients.llm.litellm_proxy_client import LiteLLMProxyClient


async def init_client_session():  # https://python-dependency-injector.ets-labs.org/providers/async.html 이를 의존하는 provider 역시 await으로 호출
    logger.debug("🟢 [ClientContainer] Initializing aiohttp ClientSession...")
    session = aiohttp.ClientSession()
    yield session
    logger.debug("🔴 [ClientContainer] Closing aiohttp ClientSession...")
    await session.close()
    logger.debug("⚫ [ClientContainer] ClientSession Closed.")


class ClientContainer(containers.DeclarativeContainer):
    """clients 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Dependency(instance_of=ClientsConfig)

    _session = providers.Resource(init_client_session)

    aiohttp_client = providers.Singleton(AioHTTPClient, config=config.provided.aiohttp, session=_session)

    chzzk_api_client = providers.Singleton(
        ChzzkAPIClient,
        config=config.provided.chzzk_api,
        http_client=aiohttp_client,
    )

    media_processor = providers.Singleton(
        MediaProcessor,
        config=config.provided.media_processor,
        http_client=aiohttp_client,
    )

    audio_loader = providers.Singleton(AudioLoader, config=config.provided.audio_loader)

    vad_client_factory = providers.Singleton(create_vad_client, model_config=config.provided.vad)

    asr_client_factory = providers.Singleton(
        create_asr_client, model_config=config.provided.asr, http_client=aiohttp_client
    )

    context_assembler = providers.Singleton(
        ContextAssembler,
        config=config.provided.context_assembler,
    )

    # prompt_builder = providers.Singleton(
    #     PromptBuilder,
    #     config=_prompt_builder_config,
    # )

    # llm_client = providers.Singleton(
    #     LiteLLMProxyClient,
    #     config=_llm_client_config,
    #     session=_session,
    # )
