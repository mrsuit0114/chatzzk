import json
import os
import time

import numpy as np
import torch
import torchaudio
from loguru import logger
from tqdm import tqdm

from audio.asr import ASR
from audio.vad import VAD
from config import AudioProcessorConfig
from data_types.context_data import ContextData


class AudioProcessor:
    def __init__(self, config: AudioProcessorConfig):
        self.data_dir = config.DATA_DIR
        self.audio_dir = config.AUDIO_DIR
        self.vad_dir = config.VAD_DIR
        self.asr_context_dir = config.ASR_CONTEXT_DIR
        self.asr_type_code = config.ASR_TYPE_CODE
        self.asr_pay_amount = config.ASR_PAY_AMOUNT

        self.asr = ASR(config.MODEL_SIZE, config.NOT_EXPECTED_ASR_LIST)
        self.vad = VAD(config.MIN_SILENCE_DURATION_MS, config.MAX_SPEECH_DURATION_S)

    def process_audio(self, video_no: int, vad_save=False):
        input_audio_path = os.path.join(self.data_dir, self.audio_dir, f"{video_no}.wav")
        output_vad_path = os.path.join(self.data_dir, self.vad_dir, f"{video_no}.jsonl")
        output_asr_context_path = os.path.join(self.data_dir, self.asr_context_dir, f"{video_no}.jsonl")

        load_start_time = time.time()
        audio, sr = torchaudio.load(input_audio_path)
        load_end_time = time.time()
        logger.info(f"audio loading time: {load_end_time - load_start_time}")

        if audio.shape[0] > 1:
            audio = torch.mean(audio, dim=0, keepdim=True)

        audio_np = audio.numpy().squeeze().astype(np.float32)

        if os.path.exists(output_vad_path):
            logger.info(f"VAD file already exists at {output_vad_path}. Loading timestamps from file.")
            timestamps = []
            with open(output_vad_path, encoding="utf-8") as f:
                for line in f:
                    timestamps.append(json.loads(line))
        else:
            logger.info("VAD file not found. Performing VAD processing.")

            vad_start_time = time.time()
            timestamps = self.vad(audio_np)
            vad_end_time = time.time()
            logger.info(f"vad total time: {vad_end_time - vad_start_time}")

            if vad_save:
                with open(output_vad_path, "w", encoding="utf-8") as f:
                    for vad in timestamps:
                        f.write(json.dumps(vad, ensure_ascii=False) + "\n")

        asr_contexts = []
        asr_start_time = time.time()
        for vad in tqdm(timestamps, desc="asr processing"):
            asr_result = "".join(self.asr(audio_np, [vad])).strip()
            if asr_result:
                timestamp_ms = (
                    vad[0] + vad[1]
                ) // 32  # vad의 기준은 샘플단위이므로 시간으로 변경하려면 샘플 -> 초 -> ms -> 평균 연산
                asr_context = ContextData(
                    timestamp_ms, asr_result, self.asr_type_code, asr_result, self.asr_pay_amount
                )
                asr_contexts.append(asr_context)
        asr_end_time = time.time()
        logger.info(f"asr total time: {asr_end_time - asr_start_time}")

        with open(output_asr_context_path, "a", encoding="utf-8") as f:
            for asr_context in asr_contexts:
                f.write(json.dumps(asr_context._asdict(), ensure_ascii=False) + "\n")

        return None
