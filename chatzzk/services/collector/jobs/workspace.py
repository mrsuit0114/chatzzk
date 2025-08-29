import shutil
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from chatzzk.services.collector.settings import collector_settings

VIDEO_FILENAME = "video.mp4"
AUDIO_FILENAME = "audio.wav"
CHAT_FILENAME = "chat.jsonl"


@dataclass
class VodWorkspacePaths:
    """VOD 처리 작업 공간의 파일 경로들을 담는 데이터 클래스."""

    base: Path
    mp4: Path = field(init=False)
    wav: Path = field(init=False)
    chat: Path = field(init=False)

    def __post_init__(self):
        # 인스턴스 생성 후 파일 경로를 자동으로 구성
        self.mp4 = self.base / VIDEO_FILENAME
        self.wav = self.base / AUDIO_FILENAME
        self.chat = self.base / CHAT_FILENAME


class VodWorkspace:
    """특정 VOD 처리를 위한 임시 작업 공간을 관리하는 클래스."""

    def __init__(self, video_no: str):
        base_temp_dir = Path(collector_settings.TEMP_DIR_BASE) / "chatzzk_processor"
        self.workspace_dir = base_temp_dir / video_no
        self.paths = VodWorkspacePaths(base=self.workspace_dir)

    def setup(self):
        """작업 공간을 준비합니다. 기존 내용이 있으면 삭제하고 새로 만듭니다."""
        if self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Set up temporary workspace: {self.workspace_dir}")

    def cleanup(self):
        """작업 공간의 모든 내용을 정리(삭제)합니다."""
        if self.workspace_dir.exists():
            try:
                shutil.rmtree(self.workspace_dir)
                logger.info(f"Cleaned up temporary workspace: {self.workspace_dir}")
            except OSError as e:
                logger.error(f"Failed to clean up workspace {self.workspace_dir}: {e}")
