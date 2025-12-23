import asyncio

import aiohttp
import instructor
from dependency_injector import containers, providers
from langfuse import Langfuse
from loguru import logger
from openai import AsyncOpenAI

from chatzzk_clients._http import AioHTTPClient
from chatzzk_clients.chzzk import ChzzkAPIClient
from chatzzk_clients.llm import ContextAssembler, LLMClient, PromptManager
from chatzzk_clients.media import MediaProcessor
from chatzzk_clients.ml.asr import create_asr_client
from chatzzk_clients.ml.audio_loader import AudioLoader
from chatzzk_clients.ml.vad import create_vad_client
from chatzzk_core.schemas.config import ClientsConfig
from chatzzk_core.schemas.config.clients import LangfuseConfig, LiteLLMConfig


async def init_client_session():  # https://python-dependency-injector.ets-labs.org/providers/async.html 이를 의존하는 provider 역시 await으로 호출
    logger.debug("🟢 [ClientContainer] Initializing aiohttp ClientSession...")
    session = aiohttp.ClientSession()
    yield session
    logger.debug("🔴 [ClientContainer] Closing aiohttp ClientSession...")
    await session.close()
    logger.debug("⚫ [ClientContainer] ClientSession Closed.")


def init_langfuse_client(config: LangfuseConfig):
    logger.debug("🟢 [ClientContainer] Initializing LangfuseClient...")
    client = Langfuse(
        public_key=config.public_key,
        secret_key=config.secret_key,
        base_url=config.base_url,
    )
    yield client
    logger.debug("🔴 [ClientContainer] Closing LangfuseClient...")
    client.flush()
    logger.debug("⚫ [ClientContainer] LangfuseClient Closed.")


def init_llm_client(config: LiteLLMConfig):
    logger.debug("🟢 [ClientContainer] Initializing LLMClient...")
    client = AsyncOpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
    )

    patched_client = instructor.from_openai(client, mode=instructor.Mode.JSON_SCHEMA)
    yield patched_client
    logger.debug("🔴 [ClientContainer] Closing LLMClient...")
    asyncio.create_task(client.close())
    logger.debug("⚫ [ClientContainer] LLMClient Closed.")


class ClientContainer(containers.DeclarativeContainer):
    """clients 패키지의 의존성을 관리하는 컨테이너"""

    config = providers.Dependency(instance_of=ClientsConfig)

    _session = providers.Resource(init_client_session)
    _langfuse_client = providers.Resource(init_langfuse_client, config=config.provided.prompt_manager)
    _llm_client = providers.Resource(init_llm_client, config=config.provided.llm_client)

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

    prompt_manager = providers.Singleton(
        PromptManager,
        langfuse_client=_langfuse_client,
        config=config.provided.prompt_manager,
    )

    llm_client = providers.Singleton(
        LLMClient,
        client=_llm_client,
        config=config.provided.llm_client,
    )
