# packages/schemas/asr.py


from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# ASR Inference API 스키마
# -------------------------------------------------------------------

# 요청(Request) 스키마는 FastAPI의 Form/File을 직접 사용하므로
# Pydantic 모델이 별도로 필요하지 않을 수 있습니다.
# 하지만 응답(Response) 스키마는 명확하게 정의하는 것이 매우 중요합니다.


class ASRTranscription(BaseModel):
    """
    단일 오디오 청크에 대한 ASR 결과
    """

    text: str = Field(..., description="전체 인식 결과 문장")
    language: str = Field(..., description="언어 코드 (e.g., 'ko', 'en')")


class ASRResponse(BaseModel):
    """
    ASR Inference API의 최종 응답 모델
    """

    task_id: str | None = Field(None, description="요청을 식별하기 위한 고유 ID")
    transcription: ASRTranscription = Field(..., description="ASR 처리 결과")


# -------------------------------------------------------------------
# 에러 응답 스키마
# -------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """
    API 에러 발생 시 공통 응답 모델
    """

    error_code: str = Field(..., description="정의된 에러 코드")
    message: str = Field(..., description="에러에 대한 설명")
