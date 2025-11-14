from dependency_injector import containers, providers

from chatzzk.services.service_implementations.speech_processing.speech_processing import SpeechProcessingService


class SpeechProcessingContainer(containers.DeclarativeContainer):
    tmp_storage = providers.Dependency()
    vod_repo = providers.Dependency()
    media_processor = providers.Dependency()
    db_session_factory = providers.Dependency()
    vad_client = providers.Dependency()
    asr_client = providers.Dependency()

    speech_processing = providers.Factory(
        SpeechProcessingService,
        tmp_storage=tmp_storage,
        vod_repo=vod_repo,
        media_processor=media_processor,
        db_session_factory=db_session_factory,
        vad_client=vad_client,
        asr_client=asr_client,
    )
