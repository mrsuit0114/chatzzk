from typing import Protocol


class VoiceAnalysis(Protocol):
    """
    단일 VOD의 오디오 데이터를 분석(VAD, ASR)하는 역할을 정의합니다.
    """

    def perform_vad(self, video_no: str) -> str:
        """
        추출된 오디오에서 음성 구간을 탐지(VAD)하고,
        결과(timestamps)를 임시 스토리지에 저장한 뒤 경로(key)를 반환합니다.
        """
        ...

    def perform_asr(self, video_no: str) -> str:
        """
        오디오와 VAD 결과를 바탕으로 음성 인식(ASR)을 수행합니다.
        결과를 영구 스토리지에 저장하고, 저장된 파일의 경로(key)를 반환합니다.
        """
        ...
