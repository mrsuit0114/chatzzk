from typing import Protocol


class PipelineLifecycle(Protocol):
    """
    VOD 처리 파이프라인의 전체 상태를 관리하고,
    최종 단계를 처리하는 역할을 정의합니다.
    """

    def update_vod_process_status(self, video_no: str, status: str) -> None:
        """
        VOD의 전체 처리 상태(예: PENDING, PROCESSING, COMPLETED, FAILED)를
        데이터베이스에 업데이트합니다.
        """
        ...

    def cleanup_temp_files(self, video_no: str) -> None:
        """
        모든 파이프라인 단계가 성공적으로 완료된 후,
        임시 스토리지에 저장되었던 파일(영상, 음성 등)을 삭제합니다.
        """
        ...
