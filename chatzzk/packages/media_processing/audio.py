from pathlib import Path

import ffmpeg
import numpy as np
import torch
import torchaudio
from loguru import logger


def extract_wav_from_video(
    video_path: str | Path,
    output_wav_path: str | Path,
    sampling_rate: int = 16000,
    audio_channels: int = 1,
) -> None:
    """
    비디오 파일에서 WAV 오디오를 추출하여 지정된 경로에 저장합니다.
    시스템에 ffmpeg 실행 파일이 설치되어 있어야 합니다.

    Args:
        video_path (str | Path): 입력 비디오 파일 경로.
        output_wav_path (str | Path): 출력 WAV 파일 경로.
        sampling_rate (int, optional): 출력 오디오의 샘플링 속도(Hz). ASR에 표준적인 16000이 기본값.
        audio_channels (int, optional): 출력 오디오 채널 수. ASR에는 모노(1)가 표준.

    Raises:
        ffmpeg.Error: ffmpeg 처리 중 오류가 발생할 경우.
        FileNotFoundError: 입력 비디오 파일이 없을 경우.
    """
    video_path = Path(video_path)
    output_wav_path = Path(output_wav_path)

    if not video_path.is_file():
        raise FileNotFoundError(f"Input video file not found at: {video_path}")

    logger.info(f"🎞️ -> 🔊 Extracting WAV from '{video_path.name}'...")
    logger.debug(f"Output settings: Sample Rate={sampling_rate}Hz, Channels={audio_channels}")

    try:
        (
            ffmpeg.input(str(video_path))
            .output(
                str(output_wav_path),
                acodec="pcm_s32le",  # WAV 포맷 (32-bit signed little-endian PCM)
                ac=audio_channels,  # 오디오 채널 (1=모노, 2=스테레오)
                ar=str(sampling_rate),  # 오디오 샘플링 레이트
            )
            .overwrite_output()  # 출력 파일이 이미 있으면 덮어쓰기
            .run(capture_stdout=True, capture_stderr=True)  # 실행 및 출력 캡처
        )
        logger.success(f"✅ Successfully extracted WAV to '{output_wav_path.name}'")

    except ffmpeg.Error as e:
        error_details = e.stderr.decode(errors="ignore").strip()
        logger.error(f"❌ ffmpeg failed to extract audio from '{video_path.name}': {error_details}")
        raise e


def load_audio(input_audio_path: str | Path, target_sr: int | None = 16000) -> tuple[np.ndarray, int]:
    """
    오디오 파일을 로드하고, NumPy 배열과 샘플링 속도를 반환합니다.
    필요 시 리샘플링과 모노 변환을 수행합니다.

    Args:
        input_audio_path (str | Path): 로드할 오디오 파일 경로.
        target_sr (int | None, optional): 목표 샘플링 속도. None이면 리샘플링 안함.

    Returns:
        Tuple[np.ndarray, int]: (오디오 데이터 배열, 최종 샘플링 속도).

    Raises:
        FileNotFoundError: 파일이 없을 경우.
        Exception: 오디오 로딩/처리에 실패할 경우.
    """
    input_path = Path(input_audio_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Audio file not found at: {input_path}")

    try:
        audio, sr = torchaudio.load(str(input_path))

        # 1. 모노 변환
        if audio.shape[0] > 1:
            audio = torch.mean(audio, dim=0, keepdim=True)

        # 2. 리샘플링 (필요 시)
        if target_sr and sr != target_sr:
            logger.info(f"🔄 Resampling audio from {sr}Hz to {target_sr}Hz")
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
            audio = resampler(audio)
            sr = target_sr  # 샘플링 속도를 목표값으로 업데이트

        # 3. NumPy 변환
        audio_np = audio.numpy().squeeze().astype(np.float32)

        logger.info(f"📊 Audio loaded: Duration={len(audio_np) / sr:.2f}s, Sample rate={sr}Hz")

        # 4. 데이터와 샘플링 속도를 함께 반환
        return audio_np, sr

    except Exception as e:
        logger.error(f"❌ Failed to load or process audio from {input_path}: {e}")
        raise
