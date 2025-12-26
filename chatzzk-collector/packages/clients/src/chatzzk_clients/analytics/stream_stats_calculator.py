import math
from collections import Counter

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

from chatzzk_core.schemas.internal.stream import BaseStreamEntry, SegmentSummaryEntry


class StreamStatsCalculator:
    """
    순수 데이터 분석 및 통계 계산을 담당하는 클래스.
    외부 의존성(DB, Storage) 없이 오직 메모리 상의 데이터 연산만 수행합니다.
    """

    def calculate_stream_metrics(
        self, entries: list[BaseStreamEntry], duration_s: int, window_size: int, sigma: float = 1.0
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
        if window_size <= 0:
            steps = 0
        else:
            steps = math.ceil(duration_ms / window_size)

        # 데이터가 없거나 영상 길이가 윈도우보다 짧은 경우
        if not entries or steps == 0:
            return {"volume": [0.0] * steps, "momentum": [0.0] * steps}

        # 1. DataFrame 변환
        df = pd.DataFrame([e.model_dump() for e in entries])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # 2. Target Window Binning (핵심 수정 사항)
        binned_counts = df["content"].resample(f"{window_size}ms").count()

        # 전체 시간 길이 맞추기 (Padding)
        full_idx = pd.date_range(start=pd.to_datetime(0, unit="ms"), periods=steps, freq=f"{window_size}ms")
        binned_counts = binned_counts.reindex(full_idx, fill_value=0)

        # 3. Gaussian Smoothing
        metrics_values = gaussian_filter1d(binned_counts.values, sigma=sigma)

        # 4. Metric 1: Volume (Min-Max Normalization -> [0, 1])
        min_v, max_v = metrics_values.min(), metrics_values.max()

        if max_v - min_v == 0:
            volume_norm = np.zeros_like(metrics_values)
        else:
            volume_norm = (metrics_values - min_v) / (max_v - min_v)

        # 5. Metric 2: Momentum (Central Difference -> Z-Score)
        gradients = np.gradient(metrics_values)
        grad_mean, grad_std = np.mean(gradients), np.std(gradients)

        if grad_std == 0:
            momentum_z = np.zeros_like(gradients)
        else:
            momentum_z = (gradients - grad_mean) / grad_std

        # 6. 포맷팅
        return {"volume": np.round(volume_norm, 2).tolist(), "momentum": np.round(momentum_z, 2).tolist()}

    def calculate_atmosphere_ratio(self, summaries: list[SegmentSummaryEntry]) -> dict[str, float]:
        """
        전체 세그먼트 중 각 분위기가 차지하는 비율(%)을 계산합니다.
        (Pie Chart 용)
        """
        if not summaries:
            return {}

        atmo_counts = Counter([s.atmosphere for s in summaries])
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
