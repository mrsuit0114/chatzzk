# tests/packages/constants/test_service_codes.py
from chatzzk.packages.constants.service_codes import (
    PipelineStep,
    StorageBucket,
    StorageObject,
    VodProcessStatus,
)


def test_storage_object_path_formatting():
    """
    목적: StorageObject의 경로 템플릿이 video_no와 함께 올바르게 포매팅되는지 테스트합니다.
    이유: 파일 경로는 데이터 저장/로드의 핵심 요소이므로, 경로 생성 로직의 정확성은 매우 중요합니다.
    """
    video_no = "123456789"

    # 테스트 내용: 각 경로 템플릿에 video_no를 적용하고 예상 경로와 일치하는지 확인합니다.
    expected_temp_video_path = f"temp/{video_no}/video.mp4"
    assert StorageObject.TEMP_VIDEO.format(video_no=video_no) == expected_temp_video_path

    expected_temp_audio_path = f"temp/{video_no}/audio.wav"
    assert StorageObject.TEMP_AUDIO.format(video_no=video_no) == expected_temp_audio_path

    expected_chat_entries_path = f"contexts/{video_no}/chat_entries.jsonl"
    assert StorageObject.CHAT_ENTRIES.format(video_no=video_no) == expected_chat_entries_path

    expected_asr_entries_path = f"contexts/{video_no}/asr_entries.jsonl"
    assert StorageObject.ASR_ENTRIES.format(video_no=video_no) == expected_asr_entries_path

    expected_summary_entries_path = f"summaries/{video_no}/summary_entries.jsonl"
    assert StorageObject.SUMMARY_ENTRIES.format(video_no=video_no) == expected_summary_entries_path

    expected_meta_summary_path = f"meta_summaries/{video_no}/meta_summary_entries.jsonl"
    assert StorageObject.META_SUMMARY_ENTRIES.format(video_no=video_no) == expected_meta_summary_path


def test_enum_values():
    # 목적: 주요 Enum 클래스들이 정의된 값을 정확하게 반환하는지 테스트합니다.
    # 이유: Enum 값은 상태 관리, DB 저장 값, API 파라미터 등 시스템 전반의 로직 분기에 사용됩니다.
    #      이 값들이 예기치 않게 변경되면 심각한 버그를 유발할 수 있습니다.

    # 테스트 내용: 각 Enum 멤버의 값이 예상되는 문자열/정수 값과 일치하는지 확인합니다.
    assert VodProcessStatus.PENDING == "PENDING"
    assert VodProcessStatus.COMPLETED == "COMPLETED"

    assert PipelineStep.CRAWL_CHAT == "crawl_chat"
    assert PipelineStep.PERFORM_ASR == "perform_asr"

    assert StorageBucket.CHZZK == "chzzk"
