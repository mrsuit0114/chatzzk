from pathlib import Path

import ffmpeg
from loguru import logger


def extract_wav_from_video(
    video_path: str | Path,
    output_wav_path: str | Path,
    sample_rate: int = 16000,
    audio_channels: int = 1,
) -> None:
    """
    비디오 파일에서 WAV 오디오를 추출하여 지정된 경로에 저장합니다.
    시스템에 ffmpeg 실행 파일이 설치되어 있어야 합니다.

    Args:
        video_path (str | Path): 입력 비디오 파일 경로.
        output_wav_path (str | Path): 출력 WAV 파일 경로.
        sample_rate (int, optional): 출력 오디오의 샘플링 속도(Hz). ASR에 표준적인 16000이 기본값.
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
    logger.debug(f"Output settings: Sample Rate={sample_rate}Hz, Channels={audio_channels}")

    try:
        (
            ffmpeg.input(str(video_path))
            .output(
                str(output_wav_path),
                acodec="pcm_s16le",  # WAV 포맷 (16-bit signed little-endian PCM)
                ac=audio_channels,  # 오디오 채널 (1=모노, 2=스테레오)
                ar=str(sample_rate),  # 오디오 샘플링 레이트
            )
            .overwrite_output()  # 출력 파일이 이미 있으면 덮어쓰기
            .run(capture_stdout=True, capture_stderr=True)  # 실행 및 출력 캡처
        )
        logger.success(f"✅ Successfully extracted WAV to '{output_wav_path.name}'")
    except Exception as e:
        logger.error(f"❌ ffmpeg failed to extract audio from '{video_path.name}': {e}")
        raise e
