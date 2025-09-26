# tests/packages/media_processing/test_audio.py

import tempfile
from pathlib import Path

import ffmpeg
import numpy as np
import pytest
import torch

from chatzzk.packages.media_processing.audio import extract_wav, load_audio


def test_extract_wav_success(mocker):
    """
    목적: extract_wav 함수가 ffmpeg을 올바른 인자로 호출하여 변환을 시도하는지 테스트합니다.
    이유: 핵심 기능인 ffmpeg 호출 로직이 정확한지, 파라미터(코덱, 채널, 샘플링 속도 등)가 올바르게 전달되는지 보장해야 합니다.
    """
    # 준비 (Arrange)
    # 1. 메서드 체이닝의 각 단계를 모킹합니다.
    mock_run = mocker.patch("ffmpeg.run")

    # overwrite_output()이 호출되면 반환될 모킹 객체
    mock_overwrite_output_result = mocker.MagicMock()
    # 이 객체의 run 메서드를 mock_run으로 설정
    mock_overwrite_output_result.run = mock_run

    # output()이 호출되면 반환될 모킹 객체
    mock_output_result = mocker.MagicMock()
    # 이 객체의 overwrite_output 메서드가 mock_overwrite_output_result 객체를 반환하도록 설정
    mock_output_result.overwrite_output.return_value = mock_overwrite_output_result

    # ffmpeg.input()이 호출되면 반환될 모킹 객체
    mock_input_result = mocker.MagicMock()
    # 이 객체의 output 메서드가 mock_output_result 객체를 반환하도록 설정
    mock_input_result.output.return_value = mock_output_result

    # ffmpeg.input 자체를 모킹하여 mock_input_result를 반환하도록 설정
    mocker.patch("ffmpeg.input", return_value=mock_input_result)

    # 2. 임시 로컬 파일 경로를 생성합니다.
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "video.mp4"
        output_path = Path(tmpdir) / "audio.wav"

        # 실행 (Act)
        extract_wav(
            input_video_path=input_path,
            output_wav_path=output_path,
            sample_rate=16000,
            audio_channels=1,
        )

        # 검증 (Assert)
        # 1. ffmpeg.input이 올바른 경로로 호출되었는지 확인합니다.
        # mocker.patch("ffmpeg.input")을 사용했으므로 바로 ffmpeg.input.assert...를 사용할 수 있습니다.
        ffmpeg.input.assert_called_once_with(str(input_path))

        # 2. .output이 올바른 경로와 오디오 옵션으로 호출되었는지 확인합니다.
        mock_input_result.output.assert_called_once_with(
            str(output_path),
            acodec="pcm_s32le",
            ac=1,
            ar="16000",
        )

        # 3. .overwrite_output()이 호출되었는지 확인합니다.
        mock_output_result.overwrite_output.assert_called_once()

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
    mock_run = mocker.patch("ffmpeg.run", side_effect=ffmpeg.Error("mocked ffmpeg error", b"", b""))

    # overwrite_output()이 호출되면 반환될 모킹 객체
    mock_overwrite_output_result = mocker.MagicMock()
    # 이 객체의 run 메서드를 mock_run으로 설정
    mock_overwrite_output_result.run = mock_run

    # output()이 호출되면 반환될 모킹 객체
    mock_output_result = mocker.MagicMock()
    # 이 객체의 overwrite_output 메서드가 mock_overwrite_output_result 객체를 반환하도록 설정
    mock_output_result.overwrite_output.return_value = mock_overwrite_output_result

    # ffmpeg.input()이 호출되면 반환될 모킹 객체
    mock_input_result = mocker.MagicMock()
    # 이 객체의 output 메서드가 mock_output_result 객체를 반환하도록 설정
    mock_input_result.output.return_value = mock_output_result

    # ffmpeg.input 자체를 모킹하여 mock_input_result를 반환하도록 설정
    mocker.patch("ffmpeg.input", return_value=mock_input_result)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "video.mp4"
        output_path = Path(tmpdir) / "audio.wav"

        # 실행 및 검증 (Act & Assert): ffmpeg.Error가 발생하는지 확인합니다.
        with pytest.raises(ffmpeg.Error):
            extract_wav(
                input_video_path=input_path,
                output_wav_path=output_path,
                sample_rate=16000,
                audio_channels=1,
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

        audio_np, sr = load_audio(audio_path, sample_rate=target_sr, audio_channels=1)

        mock_decoder_class.assert_called_with(audio_path, sample_rate=target_sr, num_channels=1)
        mock_decoder_instance.get_all_samples.assert_called()
        assert isinstance(audio_np, np.ndarray)
        assert sr == target_sr
        assert audio_np.shape == (target_sr,)

    mock_decoder_class.reset_mock()
    mock_decoder_instance.get_all_samples.reset_mock()

    # 2. bytes 입력 케이스
    fake_bytes = b"fake_wav_bytes"
    audio_np, sr = load_audio(fake_bytes, sample_rate=target_sr, audio_channels=1)
    mock_decoder_class.assert_called_with(fake_bytes, sample_rate=target_sr, num_channels=1)
    mock_decoder_instance.get_all_samples.assert_called()
    assert isinstance(audio_np, np.ndarray)
    assert sr == target_sr
    assert audio_np.shape == (target_sr,)

    mock_decoder_class.reset_mock()
    mock_decoder_instance.get_all_samples.reset_mock()

    # 3. Tensor 입력 케이스
    fake_tensor = torch.randn(1, target_sr)
    audio_np, sr = load_audio(fake_tensor, sample_rate=target_sr, audio_channels=1)
    mock_decoder_class.assert_called_with(fake_tensor, sample_rate=target_sr, num_channels=1)
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
