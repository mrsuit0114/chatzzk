import math
from collections import Counter

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

from chatzzk_core.schemas.internal import SegmentSummaryDict, StreamEntryDict


class StreamStatsCalculator:
    """
    순수 데이터 분석 및 통계 계산을 담당하는 클래스.
    외부 의존성(DB, Storage) 없이 오직 메모리 상의 데이터 연산만 수행합니다.
    """

    def calculate_stream_metrics(
        self, entries: list[StreamEntryDict], duration_s: int, window_size: int, sigma: float = 1.0
    ) -> dict[str, list[float]]:
        """
        BaseStreamEntry 리스트를 분석하여 정규화된 Volume과 Momentum을 반환합니다.

        duration_s: 스트림의 전체 길이 (초 단위)
        window_size: 집계 윈도우 크기 (밀리초 단위)
        sigma: 가우시안 스무딩 시그마 값

        [Process]
        1. Target Window Binning: 지정된 윈도우 크기(30s, 5m)로 즉시 집계
        2. Smoothing: 집계된 윈도우 간의 연속성을 위해 스무딩 적용
        3. Metrics: Volume 및 Momentum 계산
        """
        duration_ms = duration_s * 1000
        steps = math.ceil(duration_ms / window_size) if window_size > 0 else 0

        # 데이터가 없거나 영상 길이가 윈도우보다 짧은 경우
        if not entries or steps == 0:
            return {"volume": [0.0] * steps, "momentum": [0.0] * steps}

        # 1. DataFrame 변환
        df = pd.DataFrame(entries)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # 2. Window Binning (Raw Count)
        binned_counts = df["content"].resample(f"{window_size}ms").count()

        full_idx = pd.date_range(
            start=pd.to_datetime(0, unit="ms"),
            periods=steps,
            freq=f"{window_size}ms",
        )
        # raw_values 확보
        raw_values = binned_counts.reindex(full_idx, fill_value=0).to_numpy(dtype=float)

        v_range = raw_values.max() - raw_values.min()
        volume_norm = (raw_values - raw_values.min()) / v_range if v_range > 0 else np.zeros_like(raw_values)

        # ✅ 2️⃣ Momentum (Smoothed)
        smoothed = gaussian_filter1d(raw_values, sigma=sigma)
        gradients = np.gradient(smoothed)

        grad_s = pd.Series(gradients)
        rolling = grad_s.rolling(window=11, center=True, min_periods=1)
        r_mean = rolling.mean()
        r_std = rolling.std()

        # 0으로 나누기 방지: std가 아주 작거나 0이면 z-score는 0
        momentum_z = (grad_s - r_mean) / r_std.replace(0, np.nan)
        momentum_z = momentum_z.fillna(0).replace([np.inf, -np.inf], 0)

        return {
            "volume": np.round(volume_norm, 2).tolist(),
            "momentum": np.round(momentum_z, 2).tolist(),
        }

    def calculate_atmosphere_ratio(self, summaries: list[SegmentSummaryDict]) -> dict[str, float]:
        """
        전체 세그먼트 중 각 분위기가 차지하는 비율(%)을 계산합니다.
        (Pie Chart 용)
        """
        if not summaries:
            return {}

        atmo_counts = Counter([s["atmosphere"] for s in summaries])
        total = sum(atmo_counts.values())

        if total == 0:
            return {}

        return {k: round((v / total) * 100, 1) for k, v in atmo_counts.items()}

    def calculate_avg_score(self, scores: dict[str, int]) -> float:
        """
        Segment의 score 딕셔너리 값들의 평균을 계산합니다.
        (Timeline Height 용)
        """
        if not scores:
            return 0.0
        # 소수점 1자리까지 반올림
        return round(sum(scores.values()) / len(scores), 1)

    def attach_peaks_to_segments(
        self,
        segments: list[SegmentSummaryDict],
        clip_stats: dict[str, list[float]],  # 30초 단위 Clip 분석 결과
        clip_window_ms: int,
        segment_window_ms: int,
    ) -> list[SegmentSummaryDict]:
        """
        Clip 단위(30s)의 통계 데이터를 기반으로
        각 Segment(5m) 구간 내의 Volume/Momentum 최대(Peak) 지점을 찾아 주입합니다.
        """
        if not segments or not clip_stats:
            return segments

        volumes = clip_stats["volume"]
        momentums = clip_stats["momentum"]

        # Clip이 Segment 안에 몇 개 들어가는지 계산 (예: 5분 / 30초 = 10개)
        ratio = segment_window_ms // clip_window_ms
        if ratio < 1:
            ratio = 1  # 예외 처리

        for i, seg in enumerate(segments):
            # 현재 세그먼트가 커버하는 Clip 배열의 인덱스 범위 계산
            start_idx = i * ratio
            end_idx = start_idx + ratio

            # 슬라이싱 (배열 범위를 벗어나도 Python은 에러 없이 처리해줌)
            seg_vols = volumes[start_idx:end_idx]
            seg_mmts = momentums[start_idx:end_idx]

            if not seg_vols:  # 데이터가 없는 경우
                continue

            # 1. Volume Peak 찾기 (구간 내 최대값의 인덱스)
            # np.argmax는 리스트에서도 동작하지만, 리스트라면 .index(max()) 등을 사용
            # 여기서는 편의상 numpy 가정이지만 list라면 아래와 같이 구현:
            v_max_val = max(seg_vols)
            v_local_idx = seg_vols.index(v_max_val)
            v_global_idx = start_idx + v_local_idx

            seg["vol_peak"] = {
                "peak_ts": v_global_idx * clip_window_ms,
                "peak_vl": v_max_val,
                "peak_mmt": momentums[v_global_idx],  # 해당 시점의 모멘텀 (최대 아닐 수 있음)
            }

            # 2. Momentum Peak 찾기
            m_max_val = max(seg_mmts)
            m_local_idx = seg_mmts.index(m_max_val)
            m_global_idx = start_idx + m_local_idx

            seg["mmt_peak"] = {
                "peak_ts": m_global_idx * clip_window_ms,
                "peak_vl": volumes[m_global_idx],  # 해당 시점의 볼륨
                "peak_mmt": m_max_val,
            }

            # 주의: seg는 Dictionary(Mutable)이므로 직접 수정됩니다.

        return segments
