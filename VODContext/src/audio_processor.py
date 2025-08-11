import json
import os
import time
from typing import Optional

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
        self.not_expected_asr_list = config.NOT_EXPECTED_ASR_LIST
        self.model_size = config.MODEL_SIZE
        self.min_silence_duration_ms = config.MIN_SILENCE_DURATION_MS
        self.max_speech_duration_s = config.MAX_SPEECH_DURATION_S
        self.whisperx_model_dir = config.WHISPERX_MODEL_DIR
        self.compute_type = config.COMPUTE_TYPE
        self.batch_size = config.BATCH_SIZE

        # Initialize ASR and VAD models
        try:
            self.asr = ASR(
                self.model_size,
                self.not_expected_asr_list,
                self.whisperx_model_dir,
                self.compute_type,
                self.batch_size,
            )
            self.vad = VAD(self.min_silence_duration_ms, self.max_speech_duration_s)
            logger.info("✅ AudioProcessor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AudioProcessor: {e}")
            raise

    def process_audio(self, video_no: int, vad_save: bool = False) -> bool:
        """Process audio with comprehensive error handling."""
        try:
            logger.info(f"🎤 Starting audio processing for video {video_no}")

            # Setup file paths
            input_audio_path = os.path.join(self.data_dir, self.audio_dir, f"{video_no}.wav")
            output_vad_path = os.path.join(self.data_dir, self.vad_dir, f"{video_no}.jsonl")
            output_asr_context_path = os.path.join(self.data_dir, self.asr_context_dir, f"{video_no}.jsonl")

            # Check input file
            if not os.path.exists(input_audio_path):
                logger.error(f"❌ Input audio file not found: {input_audio_path}")
                return False

            # Ensure output directories exist
            os.makedirs(os.path.dirname(output_vad_path), exist_ok=True)
            os.makedirs(os.path.dirname(output_asr_context_path), exist_ok=True)

            # Load audio
            audio_data = self._load_audio(input_audio_path)
            if audio_data is None:
                return False

            # Process VAD
            timestamps = self._process_vad(audio_data, output_vad_path, vad_save)
            if not timestamps:
                logger.error("❌ VAD processing failed")
                return False

            # Process ASR
            asr_contexts = self._process_asr(audio_data, timestamps)
            if asr_contexts is None:
                return False

            # Save ASR contexts
            success = self._save_asr_contexts(asr_contexts, output_asr_context_path)
            if success:
                logger.info(f"✅ Audio processing completed for video {video_no}")
                return True
            else:
                logger.error(f"❌ Failed to save ASR contexts for video {video_no}")
                return False

        except Exception as e:
            logger.error(f"❌ Unexpected error during audio processing for video {video_no}: {e}")
            return False

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

    def _process_vad(self, audio_data: np.ndarray, output_vad_path: str, vad_save: bool) -> Optional[list[tuple]]:
        """Process Voice Activity Detection."""
        try:
            if os.path.exists(output_vad_path):
                logger.info(f"📁 VAD file already exists at {output_vad_path}. Loading timestamps...")
                timestamps = self._load_vad_timestamps(output_vad_path)
                if timestamps:
                    logger.info(f"✅ Loaded {len(timestamps)} VAD timestamps from file")
                    return timestamps
                else:
                    logger.warning("⚠️ Failed to load VAD timestamps, reprocessing...")

            logger.info("🎯 Performing VAD processing...")
            vad_start_time = time.time()
            timestamps = self.vad(audio_data)
            vad_end_time = time.time()

            if not timestamps:
                logger.warning("⚠️ No speech segments detected")
                return []

            logger.info(f"⏱️ VAD processing time: {vad_end_time - vad_start_time:.2f}s")
            logger.info(f"🎯 Detected {len(timestamps)} speech segments")

            # Save VAD results if requested
            if vad_save:
                success = self._save_vad_timestamps(timestamps, output_vad_path)
                if not success:
                    logger.warning("⚠️ Failed to save VAD timestamps")

            return timestamps

        except Exception as e:
            logger.error(f"❌ VAD processing failed: {e}")
            return None

    def _load_vad_timestamps(self, vad_path: str) -> Optional[list[tuple]]:
        """Load VAD timestamps from file."""
        try:
            timestamps = []
            with open(vad_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        timestamps.append(json.loads(line))
            return timestamps
        except Exception as e:
            logger.error(f"❌ Failed to load VAD timestamps: {e}")
            return None

    def _save_vad_timestamps(self, timestamps: list[tuple], output_path: str) -> bool:
        """Save VAD timestamps to file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for timestamp in timestamps:
                    f.write(json.dumps(timestamp, ensure_ascii=False) + "\n")
            logger.info(f"💾 VAD timestamps saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save VAD timestamps: {e}")
            return False

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
                                type_code=self.asr_type_code,
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

    def _save_asr_contexts(self, asr_contexts: list[ContextData], output_path: str) -> bool:
        """Save ASR contexts to file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for context in asr_contexts:
                    f.write(json.dumps(context._asdict(), ensure_ascii=False) + "\n")
            logger.info(f"💾 ASR contexts saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save ASR contexts: {e}")
            return False
