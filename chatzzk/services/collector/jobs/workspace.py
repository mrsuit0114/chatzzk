import shutil
from contextlib import contextmanager
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


@contextmanager
def temporary_vod_workspace(video_no: str):
    """
    특정 VOD 처리를 위한 임시 작업 공간을 제공하고,
    작업 완료 후 자동으로 정리하는 컨텍스트 매니저.
    """
    base_temp_dir = Path(collector_settings.TEMP_DIR_BASE) / "chatzzk_processor"
    workspace_dir = base_temp_dir / video_no

    # --- 진입 (__enter__) ---
    try:
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created temporary workspace: {workspace_dir}")

        # 워크스페이스 내 파일 경로들을 담은 객체를 yield
        yield VodWorkspacePaths(base=workspace_dir)

    finally:
        # --- 종료 (__exit__) ---
        # 성공/실패 여부와 관계없이 항상 실행됨
        if workspace_dir.exists():
            try:
                shutil.rmtree(workspace_dir)
                logger.info(f"Cleaned up temporary workspace: {workspace_dir}")
            except OSError as e:
                logger.error(f"Failed to clean up workspace {workspace_dir}: {e}")
