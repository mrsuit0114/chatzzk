# vad는 sample을 기준으로 구분되어 있으므로 wav를 메모리에 올리고 구간에따라 audio[start:end]로 asr 실행
# timestamp는 start와 end를 16000으로 나눈 값의 평균으로 계산하여 {"full_context": [{"timestamp": timestamp, "text": asr_result, "pay_amout":-1}]} 형태로 저장
# asr저장된 결과와 chats의 결과가 똑같은 구조를 가지므로 timestamp를 기준으로 정렬된 full_context를 구축하여 저장

import json

import numpy as np
import torch
import torchaudio
import whisperx
from loguru import logger
from tqdm import tqdm


class ASR:
    COMPUTE_TYPE = "float16"
    BATCH_SIZE = 4

    def __init__(self, model_size: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self._load_model(model_size)

    def _load_model(self, model_size: str):
        model = whisperx.load_model(model_size, device=self.device, compute_type=self.COMPUTE_TYPE)
        if model is None:
            logger.error("Failed to load whisperx model")
            raise ValueError("Failed to load whisperx model")
        logger.info("WhisperX model loaded successfully")
        return model

    def _process_audio(self, audio_data: np.ndarray) -> str:
        """
        Transcribe a segment of audio data into text.

        Args:
            audio_data (np.ndarray): A numpy array containing audio waveform data.

        Returns:
            str: The transcribed text from the audio segment.
        """
        result = self.model.transcribe(audio_data, batch_size=self.BATCH_SIZE, language="ko")
        text = "".join([res["text"] for res in result["segments"]])
        return text

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        results = []
        for start, end in timestamps:
            audio_segment = audio_data[start:end]
            results.append(self._process_audio(audio_segment))
        return results


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
            {"timestamp": (start + end) // 32, "text": asr_result, "pay_amount": -1}
        )  # // 2(for avg) // 16000(sr) * 1000(sec to ms)

    full_context = []

    i, j = 0, 0
    while i < len(chat_context) and j < len(asr_context):
        if chat_context[i]["timestamp"] < asr_context[j]["timestamp"]:
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
