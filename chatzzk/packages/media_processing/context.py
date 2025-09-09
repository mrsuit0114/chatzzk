from pathlib import Path

from loguru import logger

from chatzzk.packages.schemas.data_models import StreamContextEntry
from chatzzk.packages.utils.file_io import load_jsonl_as_models


def merge_context_files(chat_context_path: str | Path, asr_context_path: str | Path) -> list[StreamContextEntry]:
    """
    타임스탬프 기준으로 정렬된 두 개의 컨텍스트 .jsonl 파일을 읽어,
    하나의 정렬된 리스트로 병합하여 반환합니다.
    """
    logger.info(f"Merging context files: '{Path(chat_context_path).name}' and '{Path(asr_context_path).name}'")

    try:
        # 파일을 바이너리 읽기 모드("rb")로 열어 orjson의 효율성을 극대화
        with open(chat_context_path, "rb") as chat_f, open(asr_context_path, "rb") as asr_f:
            chat_entries = load_jsonl_as_models(chat_f, StreamContextEntry)
            asr_entries = load_jsonl_as_models(asr_f, StreamContextEntry)

        merged = []
        i, j = 0, 0
        len_chat, len_asr = len(chat_entries), len(asr_entries)

        while i < len_chat and j < len_asr:
            if chat_entries[i].timestamp_ms <= asr_entries[j].timestamp_ms:
                merged.append(chat_entries[i])
                i += 1
            else:
                merged.append(asr_entries[j])
                j += 1

        # 남은 항목 추가
        if i < len_chat:
            merged.extend(chat_entries[i:])
        if j < len_asr:
            merged.extend(asr_entries[j:])

        return merged

    except FileNotFoundError as e:
        logger.error(f"Context file not found: {e}")
        return []
    except Exception as e:
        logger.opt(exception=True).error(f"An error occurred during context merge: {e}")
        raise
