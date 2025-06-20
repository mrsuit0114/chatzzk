import json
import re
from typing import Optional

NOT_EXPECTED_ASR = [
    "MBC",
    "스토리였습니다",
    "세계였습니다",
    "시청해주셔서",
    "고맙습니다",
    "감사합니다",
    "날씨였습니다",
    "기상캐스터",
    "수고하셨습니다",
]

PROMPT_CMD_TO_TYPE_CODE = {"chat": 100, "donation": 1000, "asr": 10000}

TYPE_CODE_TO_PROMPT_CMD = {v: k.upper() for k, v in PROMPT_CMD_TO_TYPE_CODE.items()}


def _preprocess_chat_message(text: str) -> str:
    # {:...:} 형태 제거
    text = re.sub(r"\{:[^:]*:\}", "", text)

    text = re.sub(r"ㅋ{2,}", "ㅋㅋ", text)
    text = re.sub(r"ㅅ{2,}", "ㅅㅅ", text)
    text = re.sub(r"ㅊ{2,}", "ㅊㅊ", text)

    return text.strip()


def _preprocess_asr(asr: str) -> Optional[str]:
    if asr == "" or any(not_expected_asr in asr for not_expected_asr in NOT_EXPECTED_ASR):
        return None

    return asr


def process_jsonl(video_id: int):
    input_file = f"./data/full_contexts/{video_id}.jsonl"
    output_file = f"./data/full_contexts/processed_{video_id}.jsonl"

    processed_data = []
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():  # 빈 줄 무시
                item = json.loads(line)
                tmp = item.copy()
                if tmp["type_code"] == 10000:
                    text = _preprocess_asr(tmp["text"])
                    if text is not None:
                        tmp["text"] = text
                        tmp["prompt_str"] = f"[{TYPE_CODE_TO_PROMPT_CMD[tmp['type_code']]}] {text}\n"
                        processed_data.append(tmp)
                else:
                    text = _preprocess_chat_message(tmp["text"])
                    if text != "":
                        tmp["text"] = text
                        tmp["prompt_str"] = f"[{TYPE_CODE_TO_PROMPT_CMD[tmp['type_code']]}] {text}\n"
                        processed_data.append(tmp)

    with open(output_file, "w", encoding="utf-8") as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return processed_data
