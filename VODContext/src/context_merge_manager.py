# jsonl 파일을 토대로 fullcontext를 구성함
# 오디오의 경우 싱크를 위한 offset을 반영할 수 있음 - 발언 이후 시청자가 반응하기 까지의 시간

import json
import os

from config import ContextMergeManagerConfig


class ContextMergeManager:
    def __init__(self, config: ContextMergeManagerConfig):
        self.data_dir = config.DATA_DIR
        self.chat_context_dir = config.CHAT_CONTEXT_DIR
        self.asr_context_dir = config.ASR_CONTEXT_DIR
        self.full_context_dir = config.FULL_CONTEXT_DIR
        self.asr_context_default_offset_ms = config.ASR_CONTEXT_DEFAULT_OFFSET_MS

    def merge_context(self, video_no: int, asr_offset_ms: int = 0):
        chat_context_path = os.path.join(self.data_dir, self.chat_context_dir, f"{video_no}.jsonl")
        asr_context_path = os.path.join(self.data_dir, self.asr_context_dir, f"{video_no}.jsonl")
        full_context_path = os.path.join(self.data_dir, self.full_context_dir, f"{video_no}.jsonl")
        merged_data = []

        with (
            open(chat_context_path, encoding="utf-8") as f_chat,
            open(asr_context_path, encoding="utf-8") as f_asr,
        ):
            line_chat = f_chat.readline()
            line_asr = f_asr.readline()

            while line_chat and line_asr:
                data_chat = json.loads(line_chat)
                data_asr = json.loads(line_asr)

                if (
                    data_chat["timestamp_ms"]
                    <= data_asr["timestamp_ms"] + self.asr_context_default_offset_ms + asr_offset_ms
                ):
                    merged_data.append(data_chat)
                    line_chat = f_chat.readline()
                else:
                    merged_data.append(data_asr)
                    line_asr = f_asr.readline()

            while line_chat:
                merged_data.append(data_chat)
                line_chat = f_chat.readline()

            while line_asr:
                merged_data.append(data_asr)
                line_asr = f_asr.readline()

        with open(full_context_path, "w", encoding="utf-8") as f_full:
            for item in merged_data:
                f_full.write(json.dumps(item, ensure_ascii=False) + "\n")

        return merged_data
