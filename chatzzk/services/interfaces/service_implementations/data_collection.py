from typing import Protocol


class DataCollection(Protocol):
    """
    단일 VOD에 대한 원본 데이터(채팅, 영상, 음성)를 수집하는 역할을 정의합니다.
    """

    def collect_chat_logs(self, video_no: str) -> str:
        """
        VOD의 전체 채팅 기록을 수집하여 영구 스토리지에 저장하고,
        저장된 파일의 경로(key)를 반환합니다.
        """
        ...

    def download_video(self, video_no: str) -> str:
        """
        VOD 영상을 다운로드하여 임시 스토리지에 업로드하고,
        저장된 파일의 경로(key)를 반환합니다.
        """
        ...

    def extract_audio(self, video_no: str) -> str:
        """
        임시 스토리지의 영상 파일에서 오디오를 WAV로 추출하여 임시 스토리지에 업로드하고,
        저장된 오디오 파일의 경로(key)를 반환합니다.
        """
        ...
