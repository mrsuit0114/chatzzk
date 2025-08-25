# # services/asr_inference_server/main.py

# from typing import Annotated  # Python 3.9+ 에서 권장

# import numpy as np
# from fastapi import FastAPI, File, Form, HTTPException, UploadFile
# from chatzzk.packages.schemas.asr import ASRResponse, ErrorResponse

# app = FastAPI()

# # ... (startup 이벤트, asr_processor 등)

# @app.post(
#     "/transcribe",
#     response_model=ASRResponse,
#     responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
# )
# async def transcribe_audio(
#     # 'tensor_bytes'라는 이름의 파일 파트(part)를 받음
#     tensor_bytes: Annotated[UploadFile, File(description="Numpy array를 직렬화한 바이너리 데이터")],

#     # 'language'라는 이름의 폼 필드(part)를 받음
#     language: Annotated[str, Form(description="추론에 사용할 언어 코드 (e.g., 'ko', 'en')")],

#     # [중요] NumPy 배열 복원을 위한 메타데이터 추가
#     shape: Annotated[str, Form(description="원본 배열의 shape (쉼표로 구분. e.g., '1,16000')")],
#     dtype: Annotated[str, Form(description="원본 배열의 dtype (e.g., 'float32')")]
# ):
#     """
#     직렬화된 Numpy array와 메타데이터를 받아 ASR 추론을 수행합니다.
#     """
#     try:
#         # 1. 메타데이터 파싱
#         try:
#             parsed_shape = tuple(map(int, shape.split(',')))
#             parsed_dtype = np.dtype(dtype)
#         except ValueError:
#             raise HTTPException(status_code=400, detail="Invalid shape or dtype format.")

#         # 2. 바이너리 데이터 읽기
#         byte_data = await tensor_bytes.read()

#         # 3. NumPy 배열로 복원
#         restored_array = np.frombuffer(byte_data, dtype=parsed_dtype).reshape(parsed_shape)

#         # 4. 추론 수행
#         # asr_processor.process 함수가 numpy 배열과 language를 받도록 수정 필요
#         result: ASRResponse = asr_processor.process(
#             audio_array=restored_array,
#             language=language
#         )

#         return result

#     except Exception:
#         # 에러 처리
#         # ...
#         pass
