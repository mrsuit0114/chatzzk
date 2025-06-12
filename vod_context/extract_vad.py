# vad를 실행하고 vod의 timestamp에 맞게 context 구축
# colab extract_vad.ipynb 참고
import json
import os
from pathlib import Path

import torch
import torchaudio
from loguru import logger
from silero_vad import get_speech_timestamps, load_silero_vad

model = load_silero_vad()
MIN_SILENCE_DURATION_MS = 500
MAX_SPEECH_DURATION_S = 30


def extract_and_save_vad(video_id: int):
    audio_path = _get_audio_file_path(video_id)
    vad_context = _get_vad_context(audio_path)
    _save_vad(video_id, vad_context)
    logger.info(f"VAD context saved for video_id: {video_id}")


def _get_vad_context(audio_path: str) -> list[tuple[int, int, int]]:
    audio, sr = torchaudio.load(audio_path)
    # Convert to mono if stereo
    if audio.shape[0] > 1:
        audio = torch.mean(audio, dim=0, keepdim=True)
    timestamps = get_speech_timestamps(
        audio, model, min_silence_duration_ms=MIN_SILENCE_DURATION_MS, max_speech_duration_s=MAX_SPEECH_DURATION_S
    )
    results = []
    for timestamp in timestamps:
        results.append((timestamp["start"], timestamp["end"], -1))
    return results


def _get_audio_file_path(video_id: int) -> str:
    audio_dir = "./data/audios"
    audio_files = [f for f in os.listdir(audio_dir) if os.path.isfile(os.path.join(audio_dir, f))]

    audio_path = None
    for file in audio_files:
        stem = Path(file).stem
        if stem == str(video_id):
            audio_path = os.path.join(audio_dir, file)
            break
    if audio_path is None:
        raise FileNotFoundError(f"No audio file found ending with video_id: {video_id}")
    return audio_path


def _save_vad(video_id, vad_context: list[tuple[int, int, int]]):
    file_path = f"./data/vads/{video_id}.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        for item in vad_context:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
