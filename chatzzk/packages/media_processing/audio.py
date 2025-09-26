from pathlib import Path

import ffmpeg
import numpy as np
from loguru import logger
from torch import Tensor
from torchcodec.decoders import AudioDecoder

from chatzzk.packages.constants.service_codes import AUDIO_CHANNELS, SAMPLE_RATE


def extract_wav(
    input_video_path: Path,
    output_wav_path: Path,
    sample_rate: int = SAMPLE_RATE,
    audio_channels: int = AUDIO_CHANNELS,
) -> None:
    """
    로컬 비디오 파일에서 WAV 오디오를 추출하여 로컬 경로에 저장합니다.
    시스템에 ffmpeg 실행 파일이 설치되어 있어야 합니다.

    Args:
        input_video_path (Path): 입력 비디오 파일의 로컬 경로.
        output_wav_path (Path): 추출된 WAV 파일을 저장할 로컬 경로.
        sample_rate (int, optional): 출력 오디오의 샘플링 속도(Hz). ASR에 표준적인 16000이 기본값.
        audio_channels (int, optional): 출력 오디오 채널 수. ASR에는 모노(1)가 표준.

    Raises:
        ffmpeg.Error: ffmpeg 처리 중 오류가 발생할 경우.
    """
    try:
        logger.info(f"🎞️ -> 🔊 Extracting WAV from '{input_video_path.name}'...")
        logger.debug(f"Output settings: Sample Rate={sample_rate}Hz, Channels={audio_channels}")

        (
            ffmpeg.input(str(input_video_path))
            .output(
                str(output_wav_path),
                acodec="pcm_s32le",  # WAV 포맷 (32-bit signed little-endian PCM)
                ac=audio_channels,  # 오디오 채널 (1=모노, 2=스테레오)
                ar=str(sample_rate),  # 오디오 샘플링 레이트
            )
            .overwrite_output()  # 출력 파일이 이미 있으면 덮어쓰기
            .run(capture_stdout=True, capture_stderr=True)  # 실행 및 출력 캡처
        )
        logger.success(f"✅ Successfully extracted WAV to '{output_wav_path.name}'")

    except ffmpeg.Error as e:
        error_details = e.stderr.decode(errors="ignore").strip()
        logger.error(f"❌ ffmpeg failed to extract audio from '{input_video_path.name}': {error_details}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process video '{input_video_path.name}' for WAV extraction: {e}")
        raise


def load_audio(
    source: Path | Tensor | bytes,
    sample_rate: int = SAMPLE_RATE,
    audio_channels: int = AUDIO_CHANNELS,
) -> tuple[np.ndarray, int]:
    """
    다양한 소스(경로, 바이트, 텐서 등)로부터 오디오를 로드하고 NumPy 배열과 샘플링 속도를 반환합니다.
    torchcodec을 통해 오디오를 로드하며, 이 과정에서 목표 샘플링 속도와 채널로 변환합니다.

    Args:
        source (AudioSource): 오디오 소스. 파일 경로(str, Path), 바이트(bytes), 파일 핸들(IO[bytes]), 텐서(Tensor) 등.
        sample_rate (int, optional): 목표 샘플링 속도(Hz). 기본값 16000.
        audio_channels (int, optional): 목표 오디오 채널 수. 기본값 1 (모노).

    Returns:
        tuple[np.ndarray, int]: (오디오 데이터 배열, 최종 샘플링 속도).

    Raises:
        TorchCodecError: 디코딩 과정에서 오류가 발생할 경우.
        Exception: 그 외 예상치 못한 오류가 발생할 경우.
    """
    try:
        decoder = AudioDecoder(source, sample_rate=sample_rate, num_channels=audio_channels)
        samples = decoder.get_all_samples()
        # torchcodec 0.0.2 버전 기준으로 samples.data는 (채널, 샘플) 형태의 텐서입니다.
        audio, sr = samples.data, samples.sample_rate

        audio_np = audio.numpy().squeeze().astype(np.float32)

        logger.info(f"📊 Audio loaded: Duration={len(audio_np) / sr:.2f}s, Sample rate={sr}Hz")

        return audio_np, sr

    except Exception as e:
        if isinstance(source, (str | Path)):
            source_info = str(source)
        logger.error(f"❌ Failed to load or process audio from '{source_info}': {e}")
        raise
