# jsonl 파일을 토대로 fullcontext를 구성함
# 오디오의 경우 싱크를 위한 offset을 반영할 수 있음 - 발언 이후 시청자가 반응하기 까지의 시간

import json
import os

from config import Config
from schemas.context_data import ContextData


class ContextMergeManager:
    def __init__(self, config: Config):
        self.chat_context_dir = config.DataDir.CHAT_CONTEXT_DIR
        self.asr_context_dir = config.DataDir.ASR_CONTEXT_DIR
        self.full_context_dir = config.DataDir.FULL_CONTEXT_DIR

    def merge_context(self, video_no: int):
        chat_context_path = os.path.join(self.chat_context_dir, f"{video_no}.jsonl")
        asr_context_path = os.path.join(self.asr_context_dir, f"{video_no}.jsonl")
        full_context_path = os.path.join(self.full_context_dir, f"{video_no}.jsonl")
        merged_data: list[ContextData] = []

        with (
            open(chat_context_path, encoding="utf-8") as f_chat,
            open(asr_context_path, encoding="utf-8") as f_asr,
        ):
            line_chat = f_chat.readline()
            line_asr = f_asr.readline()

            while line_chat and line_asr:
                data_chat = ContextData.model_validate(json.loads(line_chat))
                data_asr = ContextData.model_validate(json.loads(line_asr))

                if data_chat.timestamp_ms <= data_asr.timestamp_ms:
                    merged_data.append(data_chat)
                    line_chat = f_chat.readline()
                else:
                    merged_data.append(data_asr)
                    line_asr = f_asr.readline()

            while line_chat:
                merged_data.append(ContextData.model_validate(json.loads(line_chat)))
                line_chat = f_chat.readline()

            while line_asr:
                merged_data.append(ContextData.model_validate(json.loads(line_asr)))
                line_asr = f_asr.readline()

        with open(full_context_path, "w", encoding="utf-8") as f_full:
            for item in merged_data:
                f_full.write(json.dumps(item.model_dump(), ensure_ascii=False) + "\n")

        return merged_data
