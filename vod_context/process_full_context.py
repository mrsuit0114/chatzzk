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


def _preprocess_chat_message(text: str) -> str:
    # {:...:} 형태 제거
    text = re.sub(r"\{:[^:]*:\}", "", text)

    if re.search(r"ㅋ{2,}", text):
        text = re.sub(r"ㅋ{2,}", "ㅋㅋ", text)

    # 'ㅅ'이 2개 이상 연속될 때만 처리
    if re.search(r"ㅅ{2,}", text):
        text = re.sub(r"ㅅ{2,}", "ㅅㅅ", text)

    # 'ㅊ'이 2개 이상 연속될 때만 처리
    if re.search(r"ㅊ{2,}", text):
        text = re.sub(r"ㅊ{2,}", "ㅊㅊ", text)

    return text.strip()


def _preprocess_asr(asr: str) -> Optional[str]:
    if any(
        not_expected_asr in asr for not_expected_asr in NOT_EXPECTED_ASR
    ):  # 발언하지 않았음에도 'MBC 기자 누구입니다.'가 나와 제외함
        return None
    if asr == "":
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
                if tmp["pay_amount"] == -1:
                    text = _preprocess_asr(tmp["text"])
                    if text is not None:
                        tmp["text"] = text
                        processed_data.append(tmp)
                else:
                    text = _preprocess_chat_message(tmp["text"])
                    if text != "":
                        tmp["text"] = text
                        processed_data.append(tmp)

    with open(output_file, "w", encoding="utf-8") as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return processed_data
