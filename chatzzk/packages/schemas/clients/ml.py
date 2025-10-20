from pydantic import BaseModel, Field


class AsrResponse(BaseModel):
    """
    Asr Inference API의 최종 응답 모델
    """

    text: str = Field(..., description="Asr 처리 결과")
    # infer_time: float = Field(..., description="Inference time") 하드웨어 문제로 시간이 자꾸 튀어서 기록하는 의미가 없음
