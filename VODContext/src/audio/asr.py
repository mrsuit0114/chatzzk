import numpy as np
import torch
import whisperx
from loguru import logger

from config import Config


class ASR:
    def __init__(self, config: Config):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_size = config.ASR.MODEL_SIZE
        self.not_expected_asr_list = config.ASR.NOT_EXPECTED_ASR_LIST
        self.model_dir = config.ASR.MODEL_DIR
        self.compute_type = config.ASR.COMPUTE_TYPE
        self.batch_size = config.ASR.BATCH_SIZE
        self.language = config.ASR.LANGUAGE

        # Check device compatibility
        if self.device == "cpu":
            logger.warning("⚠️ ASR will run on CPU - this may be very slow!")
            logger.warning("💡 Consider using GPU for better performance")

        # Load model
        self.model = self._load_model()
        if self.model is None:
            raise RuntimeError("Failed to initialize ASR model")

    def _load_model(self):
        """Load WhisperX model with error handling."""
        try:
            logger.info(f"🔄 Loading WhisperX model: {self.model_size}")
            logger.info(f"📍 Model directory: {self.model_dir}")
            logger.info(f"⚙️ Compute type: {self.compute_type}")
            logger.info(f"📦 Batch size: {self.batch_size}")

            model = whisperx.load_model(
                self.model_size, device=self.device, compute_type=self.compute_type, download_root=self.model_dir
            )

            if model is None:
                logger.error("❌ Failed to load WhisperX model")
                return None

            logger.info("✅ WhisperX model loaded successfully")
            return model

        except Exception as e:
            logger.error(f"❌ Failed to load WhisperX model: {e}")
            return None

    def _process_audio(self, audio_data: np.ndarray) -> str:
        try:
            if len(audio_data) == 0:
                logger.warning("⚠️ Empty audio segment provided")
                return ""

            # Ensure audio is in the correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
                logger.debug("🔧 Audio normalized")

            result = self.model.transcribe(audio_data, batch_size=self.batch_size, language="ko")

            if not result or "segments" not in result:
                logger.warning("⚠️ No transcription result")
                return ""

            # Extract text from segments
            text = "".join([res["text"] for res in result["segments"]]).strip()
            return text

        except Exception as e:
            logger.error(f"❌ ASR transcription failed: {e}")
            return ""

    def _is_not_expected_asr(self, text: str) -> bool:
        if any(not_expected_asr in text for not_expected_asr in self.not_expected_asr_list):
            return True
        return False

    def __call__(self, audio_data: np.ndarray, timestamps: list[tuple[int, int]]) -> list[str]:
        try:
            if not timestamps:
                logger.warning("⚠️ No timestamps provided for ASR")
                return []

            results = []

            for i, (start, end) in enumerate(timestamps):
                try:
                    # Validate timestamp bounds
                    if start < 0 or end > len(audio_data) or start >= end:
                        logger.warning(
                            f"⚠️ Invalid timestamp {i}: start={start}, end={end}, audio_length={len(audio_data)}"
                        )
                        results.append("")
                        continue

                    # Extract audio segment
                    audio_segment = audio_data[start:end]

                    # Process segment
                    processed_asr = self._process_audio(audio_segment)

                    # Filter unwanted content
                    if processed_asr and not self._is_not_expected_asr(processed_asr):
                        results.append(processed_asr)
                    else:
                        results.append("")

                except Exception as e:
                    logger.error(f"❌ Failed to process ASR segment {i}: {e}")
                    results.append("")
                    continue

            return results

        except Exception as e:
            logger.error(f"❌ ASR processing failed: {e}")
            return [""] * len(timestamps) if timestamps else []
