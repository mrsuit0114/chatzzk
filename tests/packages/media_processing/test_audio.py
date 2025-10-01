# tests/packages/media_processing/test_audio.py

import tempfile
from pathlib import Path

import ffmpeg
import numpy as np
import pytest
import torch

from chatzzk.packages.constants.service_codes import AUDIO_CHANNELS, SAMPLE_RATE
from chatzzk.packages.media_processing.audio import extract_wav, load_audio


def test_extract_wav_success(mocker):
    """
    목적: extract_wav 함수가 ffmpeg을 올바른 인자로 호출하여 변환을 시도하는지 테스트합니다.
    이유: 핵심 기능인 ffmpeg 호출 로직이 정확한지, 파라미터(코덱, 채널, 샘플링 속도 등)가 올바르게 전달되는지 보장해야 합니다.
    """
    # 준비 (Arrange)
    # 1. 메서드 체이닝의 각 단계를 모킹합니다.
    mock_run = mocker.patch("chatzzk.packages.media_processing.audio.ffmpeg.run")

    # overwrite_output()이 호출되면 반환될 모킹 객체
    mock_overwrite_output = mocker.MagicMock()
    mock_overwrite_output.run = mock_run
    mock_output = mocker.MagicMock()
    mock_output.overwrite_output.return_value = mock_overwrite_output
    mock_input = mocker.MagicMock()
    mock_input.output.return_value = mock_output

    # ffmpeg.input 자체를 모킹하여 mock_input_result를 반환하도록 설정
    mocker.patch("chatzzk.packages.media_processing.audio.ffmpeg.input", return_value=mock_input)

    # 2. 임시 로컬 파일 경로를 생성합니다.
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "video.mp4"
        output_path = Path(tmpdir) / "audio.wav"

        extract_wav(
            input_video_path=input_path,
            output_wav_path=output_path,
        )

        # 1. ffmpeg.input이 올바른 경로로 호출되었는지 확인합니다.
        ffmpeg.input.assert_called_once_with(str(input_path))

        # 2. .output이 올바른 경로와 오디오 옵션으로 호출되었는지 확인합니다.
        mock_input.output.assert_called_once_with(
            str(output_path),
            acodec="pcm_s32le",
            ac=1,
            ar=str(16000),
        )

        # 3. .overwrite_output()이 호출되었는지 확인합니다.
        mock_output.overwrite_output.assert_called_once()

        # 4. 최종적으로 .run()이 호출되었는지 확인합니다.
        mock_run.assert_called_once()


def test_extract_wav_ffmpeg_error(mocker):
    """
    목적: ffmpeg 실행 중 에러가 발생했을 때, 함수가 해당 예외를 그대로 다시 발생시키는지 테스트합니다.
    이유: 외부 도구의 실패가 시스템에 조용히 무시되지 않고, 상위 호출자에게 명확히 전달되어야 합니다.
    """
    # 준비 (Arrange): ffmpeg.run이 ffmpeg.Error를 발생시키도록 설정합니다.
    # 1. 메서드 체이닝의 각 단계를 모킹합니다.
    # mock_run의 side_effect를 ffmpeg.Error로 설정합니다.
    mock_ffmpeg = mocker.patch("chatzzk.packages.media_processing.audio.ffmpeg")

    # run이 호출될 때 ffmpeg.Error 발생
    mock_ffmpeg.Error = Exception  # 필요 시 ffmpeg.Error도 정의
    mock_run = mocker.MagicMock(side_effect=mock_ffmpeg.Error("mocked ffmpeg error"))

    # overwrite_output() 호출 시 run이 호출되는 구조
    mock_overwrite_output = mocker.MagicMock()
    mock_overwrite_output.run = mock_run
    mock_output = mocker.MagicMock()
    mock_output.overwrite_output.return_value = mock_overwrite_output
    mock_input = mocker.MagicMock()
    mock_input.output.return_value = mock_output

    # ffmpeg.input() 호출 시 mock_input 반환
    mock_ffmpeg.input.return_value = mock_input

    # 임시 디렉토리에서 테스트
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "video.mp4"
        output_path = Path(tmpdir) / "audio.wav"

        with pytest.raises(mock_ffmpeg.Error):
            extract_wav(
                input_video_path=input_path,
                output_wav_path=output_path,
                sample_rate=SAMPLE_RATE,
                audio_channels=AUDIO_CHANNELS,
            )


class MockSamples:
    """torchcodec의 decoder.get_all_samples()가 반환하는 객체를 흉내 내는 Mock 클래스"""

    def __init__(self, data, sample_rate):
        self.data = data
        self.sample_rate = sample_rate


def test_load_audio_with_torchcodec(mocker):
    """
    목적: torchcodec.AudioDecoder를 사용하여 오디오를 로드, 리샘플링, 채널 변환하는 로직을 테스트합니다.
    이유: torchcodec 라이브러리를 올바른 인자(경로, 샘플링 속도, 채널)로 호출하고, 그 결과물을 후처리를 위해 numpy 배열로 잘 변환하는지 보장해야 합니다.
    """
    # 준비 (Arrange)
    target_sr = 16000
    mock_audio_tensor = torch.randn(1, target_sr)  # 1채널, 16000 샘플
    mock_samples = MockSamples(data=mock_audio_tensor, sample_rate=target_sr)

    # AudioDecoder 클래스와 그 인스턴스의 get_all_samples 메소드를 Mocking합니다.
    mock_decoder_instance = mocker.MagicMock()
    mock_decoder_instance.get_all_samples.return_value = mock_samples
    mock_decoder_class = mocker.patch(
        "chatzzk.packages.media_processing.audio.AudioDecoder", return_value=mock_decoder_instance
    )

    # 1. 파일 경로 입력 케이스
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_file:
        audio_path = Path(tmp_file.name)

        audio_np, sr = load_audio(audio_path, sample_rate=target_sr, audio_channels=AUDIO_CHANNELS)

        mock_decoder_class.assert_called_with(audio_path, sample_rate=target_sr, num_channels=AUDIO_CHANNELS)
        mock_decoder_instance.get_all_samples.assert_called()
        assert isinstance(audio_np, np.ndarray)
        assert sr == target_sr
        assert audio_np.shape == (target_sr,)

    mock_decoder_class.reset_mock()
    mock_decoder_instance.get_all_samples.reset_mock()

    # 2. bytes 입력 케이스
    fake_bytes = b"fake_wav_bytes"
    audio_np, sr = load_audio(fake_bytes, sample_rate=target_sr, audio_channels=AUDIO_CHANNELS)
    mock_decoder_class.assert_called_with(fake_bytes, sample_rate=target_sr, num_channels=AUDIO_CHANNELS)
    mock_decoder_instance.get_all_samples.assert_called()
    assert isinstance(audio_np, np.ndarray)
    assert sr == target_sr
    assert audio_np.shape == (target_sr,)

    mock_decoder_class.reset_mock()
    mock_decoder_instance.get_all_samples.reset_mock()

    # 3. Tensor 입력 케이스
    fake_tensor = torch.randn(1, target_sr)
    audio_np, sr = load_audio(fake_tensor, sample_rate=target_sr, audio_channels=AUDIO_CHANNELS)
    mock_decoder_class.assert_called_with(fake_tensor, sample_rate=target_sr, num_channels=AUDIO_CHANNELS)
    mock_decoder_instance.get_all_samples.assert_called()
    assert isinstance(audio_np, np.ndarray)
    assert sr == target_sr
    assert audio_np.shape == (target_sr,)


def test_load_audio_from_file_torchcodec_error(mocker):
    """
    목적: torchcodec 디코딩 중 에러가 발생했을 때, 함수가 예외를 올바르게 전파하는지 테스트합니다.
    이유: 외부 라이브러리의 실패가 시스템에 조용히 무시되지 않고, 상위 호출자에게 명확히 전달되어야 합니다.
    """
    # 준비 (Arrange): AudioDecoder 초기화 시 에러를 발생시키도록 설정합니다.
    mocker.patch("chatzzk.packages.media_processing.audio.AudioDecoder", side_effect=RuntimeError("decoding failed"))

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_file:
        audio_path = Path(tmp_file.name)

        # 실행 및 검증 (Act & Assert): RuntimeError가 발생하는지 확인합니다.
        with pytest.raises(RuntimeError, match="decoding failed"):
            load_audio(audio_path)
