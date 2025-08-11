import json

import numpy as np
import torchaudio
from tqdm import tqdm

from audio import ASR


def apply_asr_to_context(video_id: int, model_size: str):
    vad_path = f"./data/vads/{video_id}.jsonl"
    chat_path = f"./data/chats/{video_id}.jsonl"
    audio_path = f"./data/audios/{video_id}.wav"
    output_path = f"./data/full_contexts/{video_id}.jsonl"

    with open(vad_path, encoding="utf-8") as f:
        vad_context = [json.loads(line) for line in f]

    with open(chat_path, encoding="utf-8") as f:
        chat_context = [json.loads(line) for line in f]

    asr_context = []
    audio, sr = torchaudio.load(audio_path)
    asr = ASR(model_size)
    audio_data_np = (
        audio.numpy().squeeze().astype(np.float32)
    )  # pcm은 범위가 -32768 ~ 32767이므로 32768로 나누어 0~1 범위로 변환하지만 torchaudio에서 이미 정규화되어있기 때문에 나누지 않음

    for vad in tqdm(vad_context, desc="Transcribing audio"):
        start, end, _ = vad
        asr_result = "".join(asr(audio_data_np, [(start, end)])).strip()
        asr_context.append(
            {"timestamp_ms": (start + end) // 32, "content": asr_result, "type_code": 10000}
        )  # // 2(for avg) // 16000(sr) * 1000(sec to ms)

    full_context = []

    i, j = 0, 0
    while i < len(chat_context) and j < len(asr_context):
        if chat_context[i]["timestamp_ms"] < asr_context[j]["timestamp_ms"]:
            full_context.append(chat_context[i])
            i += 1
        else:
            full_context.append(asr_context[j])
            j += 1

    while i < len(chat_context):
        full_context.append(chat_context[i])
        i += 1

    while j < len(asr_context):
        full_context.append(asr_context[j])
        j += 1

    with open(output_path, "w", encoding="utf-8") as f:
        for item in full_context:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
