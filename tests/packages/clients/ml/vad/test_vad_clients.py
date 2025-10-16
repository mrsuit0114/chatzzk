from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from chatzzk.packages.clients.ml.vad.silero_vad_client import SileroVadClient, init_vad_worker
from chatzzk.packages.schemas.config.ml import SileroVadConfig


@pytest.fixture
def silero_vad_config() -> SileroVadConfig:
    """테스트용 `SileroVadConfig` 객체를 생성합니다."""
    return SileroVadConfig(
        vad_implementation="silero",
        min_silence_duration_ms=500,
        max_speech_duration_s=30,
        min_silence_duration_samples=8000,  # 500ms * 16kHz
        threshold=0.5,
        sample_chunk_size=64,
        overlap_num=5,
        max_workers=4,
    )


@pytest.fixture
def vad_client(silero_vad_config: SileroVadConfig) -> SileroVadClient:
    """테스트용 `SileroVadClient` 객체를 생성합니다."""
    with patch("chatzzk.packages.clients.ml.vad.silero_vad_client.ProcessPoolExecutor"):
        client = SileroVadClient(config=silero_vad_config)
    return client


@patch("chatzzk.packages.clients.ml.vad.silero_vad_client.ProcessPoolExecutor")
def test_client_initialization(mock_executor, silero_vad_config):
    """
    목적: 클라이언트 초기화 시, ProcessPoolExecutor가 올바른 초기화 함수와 함께 생성되는지 테스트합니다.
    검증: `ProcessPoolExecutor`가 `max_workers`와 `initializer` 인자를 정확히 전달받아 호출되는지 확인합니다.
    """
    SileroVadClient(config=silero_vad_config)
    mock_executor.assert_called_once_with(max_workers=silero_vad_config.max_workers, initializer=init_vad_worker)


@pytest.mark.asyncio
@patch("chatzzk.packages.clients.ml.vad.silero_vad_client.asyncio.get_running_loop")
async def test_detect_speech_orchestration(mock_get_loop, vad_client: SileroVadClient, silero_vad_config):
    """
    목적: detect_speech가 분할, 병렬처리, 병합의 전체 과정을 올바르게 조율하는지 테스트합니다.
    검증: 오디오를 분할하고, 각 조각을 병렬 실행 요청하며, 결과를 받아 병합 함수를 호출하는지 확인합니다.
    """
    # --- Arrange ---
    # loop.run_in_executor 모킹
    mock_loop_instance = MagicMock()
    # 각 chunk에 대한 Vad 결과를 실제 데이터 타입인 dict의 리스트로 모킹
    mock_run_in_executor = AsyncMock(
        side_effect=[
            [{"start": 16000, "end": 32000}],
            [{"start": 8000, "end": 24000}],
            [{"start": 0, "end": 16000}],
        ]
    )

    expected_results = [
        [{"start": 16000, "end": 32000}],
        [{"start": 8000, "end": 24000}],
        [{"start": 0, "end": 16000}],
    ]
    mock_loop_instance.run_in_executor = mock_run_in_executor
    mock_get_loop.return_value = mock_loop_instance

    # _split_audio와 _combine_chunk_timestamps 메소드도 모킹하여 순수하게 오케스트레이션만 테스트
    chunk_starts = [0, 400000, 800000]
    split_return = ([np.array([1]), np.array([2]), np.array([3])], chunk_starts)
    merge_return = [{"start": 16000, "end": 424000}]

    with (
        patch.object(vad_client, "_split_audio", return_value=split_return) as mock_split,
        patch.object(vad_client, "_combine_chunk_timestamps", return_value=merge_return) as mock_merge,
    ):
        audio_np = np.random.rand(16000 * 70)

        # --- Act ---
        final_result = await vad_client.detect_speech(audio_np)

        # --- Assert ---
        # 1. 오디오 분할 함수가 호출되었는가?
        mock_split.assert_called_once_with(audio_np)

        # 2. 각 chunk에 대해 run_in_executor가 호출되었는가? (3번)
        assert mock_run_in_executor.call_count == 3

        # 3. 병합 함수가 gather의 결과와 함께 호출되었는가?
        mock_merge.assert_called_once_with(
            expected_results,  # gather의 결과
            chunk_starts,
            silero_vad_config.min_silence_duration_samples,
        )

        # 4. 최종 결과가 병합 함수의 반환값과 일치하는가?
        assert final_result == merge_return


class TestSplitAudio:
    """_split_audio 메서드의 단위 테스트 클래스"""

    def test_split_audio_even_division(self, vad_client: SileroVadClient):
        """
        목적: 오디오 길이가 max_workers로 나누어 떨어지는 경우, 오디오가 정확히 분할되는지 테스트합니다.
        검증: 생성된 청크의 수, 각 청크의 시작/끝 위치, 오버랩 적용 여부를 확인합니다.
        """
        # 4개의 워커, 각 청크는 1000 샘플, 총 4000 샘플
        vad_client.config.max_workers = 4
        vad_client.config.sample_chunk_size = 100
        vad_client.config.overlap_num = 1
        audio_np = np.zeros(4000)

        chunks, starts = vad_client._split_audio(audio_np)

        assert len(chunks) == 4
        assert len(starts) == 4
        assert starts == [0, 1000, 2000, 3000]
        # 첫번째 청크: 0 ~ 1000 + overlap(100)
        assert len(chunks[0]) == 1100
        # 마지막 청크: 3000 ~ 4000
        assert len(chunks[3]) == 1000

    def test_split_audio_shorter_than_one_chunk(self, vad_client: SileroVadClient):
        """
        목적: 오디오 길이가 단일 청크 크기보다 작은 경우를 테스트합니다.
        """
        vad_client.config.max_workers = 4
        audio_np = np.zeros(63)

        chunks, starts = vad_client._split_audio(audio_np)

        assert len(chunks) == 4
        assert starts == [0, 0, 0, 0]
        assert len(chunks[0]) == 63
        assert len(chunks[1]) == 63
        assert len(chunks[2]) == 63
        assert len(chunks[3]) == 63


class TestCombineTimestamps:
    """_combine_chunk_timestamps 메서드의 단위 테스트 클래스"""

    @pytest.mark.parametrize(
        "chunk_results, chunk_starts, min_silence_samples, expected",
        [
            (
                # --- 시나리오 1: 병합이 필요 없는 경우 ---
                # 청크 0: (1000, 2000)
                # 청크 1: (11000, 12000) -> 이전 청크와 간격이 큼
                [[{"start": 1000, "end": 2000}], [{"start": 1000, "end": 2000}]],
                [0, 10000],
                8000,
                [(1000, 2000), (11000, 12000)],
            ),
            (
                # --- 시나리오 2: 청크 경계에서 병합이 필요한 경우 ---
                # 청크 0: (9000, 10000)
                # 청크 1: (100, 2000) -> 절대 시간으로 (10100, 12000)
                # 10100 - 10000 = 100 <= min_silence_samples(8000) -> 병합!
                [[{"start": 9000, "end": 10000}], [{"start": 100, "end": 2000}]],
                [0, 10000],
                8000,
                [(9000, 12000)],
            ),
            (
                # --- 시나리오 3: 일부 청크에 결과가 없는 경우 ---
                [[{"start": 1000, "end": 2000}], [], [{"start": 5000, "end": 6000}]],
                [0, 10000, 20000],
                8000,
                [(1000, 2000), (25000, 26000)],
            ),
            (
                # --- 시나리오 4: 모든 청크에 결과가 없는 경우 ---
                [[], [], []],
                [0, 10000, 20000],
                8000,
                [],
            ),
            (
                # --- 시나리오 5: 첫 청크가 비어있는 경우 ---
                [[], [{"start": 1000, "end": 2000}]],
                [0, 10000],
                8000,
                [(11000, 12000)],
            ),
            (
                # --- 시나리오 6: 여러 세그먼트가 포함된 복잡한 병합 ---
                # 청크 0: (1000, 2000), (8000, 9500)
                # 청크 1: (500, 1500) -> 절대 (10500, 11500). 10500-9500=1000 -> 병합
                # 병합 결과: (8000, 11500)
                # 청크 1의 두번째 세그먼트: (3000, 4000) -> 절대 (13000, 14000)
                [
                    [{"start": 1000, "end": 2000}, {"start": 8000, "end": 9500}],
                    [{"start": 500, "end": 1500}, {"start": 3000, "end": 4000}],
                ],
                [0, 10000],
                8000,
                [(1000, 2000), (8000, 11500), (13000, 14000)],
            ),
        ],
    )
    def test_merging_scenarios(
        self, vad_client: SileroVadClient, chunk_results, chunk_starts, min_silence_samples, expected
    ):
        """
        목적: 다양한 시나리오에 대해 _combine_chunk_timestamps 메서드가 정확히 동작하는지 테스트합니다.
        검증: 각 시나리오(병합 필요/불필요, 빈 청크 포함 등)에 대해 예상된 병합 결과를 반환하는지 확인합니다.
        """
        result = vad_client._combine_chunk_timestamps(chunk_results, chunk_starts, min_silence_samples)
        assert result == expected
