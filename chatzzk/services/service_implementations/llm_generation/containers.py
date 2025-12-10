from dependency_injector import containers, providers

from chatzzk.services.service_implementations.llm_generation.llm_generation import LLMGenerationService


class LLMGenerationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_session_factory = providers.Dependency()
    tmp_storage = providers.Dependency()
    vod_repo = providers.Dependency()
    channel_repo = providers.Dependency()
    platform_repo = providers.Dependency()
    prompt_builder = providers.Dependency()
    llm_client = providers.Dependency()

    llm_generation_service = providers.Factory(
        LLMGenerationService,
        db_session_factory=db_session_factory,
        tmp_storage=tmp_storage,
        vod_repo=vod_repo,
        channel_repo=channel_repo,
        platform_repo=platform_repo,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
    )
