import os
import time
from typing import List, Optional, Tuple

import numpy as np
import torch
import torchaudio
from common.schemas.context_data import ContextData
from common.schemas.service_codes import ASR_PAY_AMOUNT, ContextType
from loguru import logger
from tqdm import tqdm

from config import Config
from processing.audio.asr import ASR
from processing.audio.vad import VAD


class AudioProcessor:
    def __init__(self, config: Config):
        self.asr_type_code = ContextType.ASR
        self.asr_pay_amount = ASR_PAY_AMOUNT

        # Initialize ASR and VAD models
        try:
            self.asr = ASR(config)
            self.vad = VAD(config)
            logger.info("✅ AudioProcessor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AudioProcessor: {e}")
            raise

    def process_audio(self, audio_path: str) -> Tuple[List[tuple], List[ContextData]]:
        """Process audio with comprehensive error handling."""
        try:
            logger.info(f"🎤 Starting audio processing for {audio_path}")

            # Check input file
            if not os.path.exists(audio_path):
                logger.error(f"❌ Input audio file not found: {audio_path}")
                raise FileNotFoundError(f"Input audio file not found: {audio_path}")

            # Load audio
            audio_data = self._load_audio(audio_path)
            if audio_data is None:
                raise ValueError("Failed to load audio data")

            # Process VAD
            timestamps = self._process_vad(audio_data)
            if not timestamps:
                logger.error("❌ VAD processing failed")
                return [], []

            # Process ASR
            asr_contexts = self._process_asr(audio_data, timestamps)
            if asr_contexts is None:
                raise ValueError("Failed to process ASR")

            logger.info(f"✅ Audio processing completed for {audio_path}")
            return timestamps, asr_contexts

        except Exception as e:
            logger.error(f"❌ Unexpected error during audio processing for {audio_path}: {e}")
            raise e

    def _load_audio(self, input_audio_path: str) -> Optional[np.ndarray]:
        """Load and preprocess audio data."""
        try:
            load_start_time = time.time()
            audio, sr = torchaudio.load(input_audio_path)
            load_end_time = time.time()
            logger.info(f"⏱️ Audio loading time: {load_end_time - load_start_time:.2f}s")

            # Convert to mono if stereo
            if audio.shape[0] > 1:
                audio = torch.mean(audio, dim=0, keepdim=True)
                logger.info("🔄 Converted stereo to mono")

            # Convert to numpy array
            audio_np = audio.numpy().squeeze().astype(np.float32)
            logger.info(f"📊 Audio shape: {audio_np.shape}, Sample rate: {sr}Hz")

            return audio_np

        except Exception as e:
            logger.error(f"❌ Failed to load audio from {input_audio_path}: {e}")
            return None

    def _process_vad(self, audio_data: np.ndarray) -> list[tuple]:
        """Process Voice Activity Detection."""
        try:
            logger.info("🎯 Performing VAD processing...")
            vad_start_time = time.time()
            timestamps = self.vad(audio_data)
            vad_end_time = time.time()

            if not timestamps:
                logger.warning("⚠️ No speech segments detected")
                return []

            logger.info(f"⏱️ VAD processing time: {vad_end_time - vad_start_time:.2f}s")
            logger.info(f"🎯 Detected {len(timestamps)} speech segments")

            return timestamps

        except Exception as e:
            logger.error(f"❌ VAD processing failed: {e}")
            raise e

    def _process_asr(self, audio_data: np.ndarray, timestamps: list[tuple]) -> Optional[list[ContextData]]:
        """Process Automatic Speech Recognition."""
        try:
            if not timestamps:
                logger.info("ℹ️ No timestamps to process for ASR")
                return []

            logger.info(f"🎤 Starting ASR processing for {len(timestamps)} segments...")
            asr_start_time = time.time()

            asr_contexts = []
            for i, (start, end) in enumerate(tqdm(timestamps, desc="ASR Processing")):
                try:
                    # Extract audio segment
                    audio_segment = audio_data[start:end]

                    # Process with ASR
                    asr_result = self.asr(audio_segment, [(0, len(audio_segment))])
                    if asr_result and len(asr_result) > 0:
                        asr_text = asr_result[0].strip()
                        if asr_text:
                            # Calculate timestamp in milliseconds
                            timestamp_ms = int((start + end) / 2 * 1000 / 16000)  # Assuming 16kHz sample rate

                            asr_context = ContextData(
                                timestamp_ms=timestamp_ms,
                                content=asr_text,
                                type_code=self.asr_type_code.value,
                                prompt_str=asr_text,
                                pay_amount=self.asr_pay_amount,
                            )
                            asr_contexts.append(asr_context)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process ASR segment {i}: {e}")
                    continue

            asr_end_time = time.time()
            logger.info(f"⏱️ ASR processing time: {asr_end_time - asr_start_time:.2f}s")
            logger.info(f"🎤 Generated {len(asr_contexts)} ASR contexts")

            return asr_contexts

        except Exception as e:
            logger.error(f"❌ ASR processing failed: {e}")
            return None
