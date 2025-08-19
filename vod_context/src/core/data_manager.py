import os
from typing import Any, List

import orjson
from common.schemas.context_data import ContextData
from loguru import logger

from config import Config


class DataManager:
    def __init__(self, config: Config):
        self.video_dir = config.DataDir.VIDEO_DIR
        self.audio_dir = config.DataDir.AUDIO_DIR
        self.chat_context_dir = config.DataDir.CHAT_CONTEXT_DIR
        self.vad_dir = config.DataDir.VAD_DIR
        self.asr_context_dir = config.DataDir.ASR_CONTEXT_DIR
        self.full_context_dir = config.DataDir.FULL_CONTEXT_DIR

    def get_video_path(self, video_no: int) -> str:
        return os.path.join(self.video_dir, f"{video_no}.mp4")

    def get_audio_path(self, video_no: int) -> str:
        return os.path.join(self.audio_dir, f"{video_no}.wav")

    def get_chat_context_path(self, video_no: int) -> str:
        return os.path.join(self.chat_context_dir, f"{video_no}.jsonl")

    def get_vad_path(self, video_no: int) -> str:
        return os.path.join(self.vad_dir, f"{video_no}.jsonl")

    def get_asr_context_path(self, video_no: int) -> str:
        return os.path.join(self.asr_context_dir, f"{video_no}.jsonl")

    def get_full_context_path(self, video_no: int) -> str:
        return os.path.join(self.full_context_dir, f"{video_no}.jsonl")

    def save_jsonl(self, data: List[Any], output_path: str, append: bool = False) -> bool:
        """Save a list of objects to a JSONL file."""
        mode = "ab" if append else "wb"
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, mode) as f:
                for item in data:
                    if hasattr(item, "model_dump_json"):
                        f.write(item.model_dump_json().encode("utf-8") + b"\n")
                    elif hasattr(item, "model_dump"):
                        f.write(orjson.dumps(item.model_dump()) + b"\n")
                    else:
                        f.write(orjson.dumps(item) + b"\n")
            logger.info(f"💾 Data saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save data to {output_path}: {e}")
            return False

    def load_jsonl(self, file_path: str) -> List[Any]:
        """Load data from a JSONL file."""
        data = []
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    if line.strip():
                        data.append(orjson.loads(line))
            return data
        except FileNotFoundError:
            logger.warning(f"⚠️ File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to load data from {file_path}: {e}")
            return []

    def load_context_data_from_jsonl(self, file_path: str) -> List[ContextData]:
        """Load ContextData objects from a JSONL file."""
        data = []
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    if line.strip():
                        data.append(ContextData.model_validate_json(line))
            return data
        except FileNotFoundError:
            logger.warning(f"⚠️ File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Failed to load ContextData from {file_path}: {e}")
            return []
