import os

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chatzzk_core.constants import (
    BucketPaths,
    StoragePaths,
    VODPipelineStatus,
    VODPipelineStepStatus,
    VODProcessingStep,
)
from chatzzk_data_access.repositories import VODRepository
from chatzzk_data_access.storages import BaseCloudStorage, LocalStorage


class VODPublishingService:
    REQUIRED_STEPS = [step for step in VODProcessingStep]

    def __init__(
        self,
        vod_repo: VODRepository,
        db_session_factory: async_sessionmaker[AsyncSession],
        tmp_storage: LocalStorage,
        cloud_storage: BaseCloudStorage,
    ):
        self.vod_repo = vod_repo
        self.db_session_factory = db_session_factory
        self.tmp_storage = tmp_storage
        self.cloud_storage = cloud_storage

    async def _evaluate_vod(self, vod_id: int) -> None:
        """
        검증 실패 시 False 반환 대신 명확한 예외를 발생시킵니다.
        """
        async with self.db_session_factory() as session:
            vod = await self.vod_repo.get_by_id(session, vod_id)

            # [수정 1] vod가 None일 경우 방어 로직 추가
            if not vod:
                raise ValueError(f"[Verify Fail] VOD {vod_id} not found.")

            if vod.pipeline_status == VODPipelineStatus.COMPLETED:
                raise ValueError(f"[Verify Fail] VOD {vod_id} is already completed.")

            # 2. 로그 상세 정보 확인
            vod_logs = await self.vod_repo.get_log_details(session, vod_id)

            if not vod_logs:
                raise ValueError(f"[Verify Fail] Pipeline logs not found for VOD {vod_id}.")

            missing_steps = []
            for step in self.REQUIRED_STEPS:
                # 상태가 COMPLETED가 아니면 실패 목록에 추가
                if vod_logs.get(step, {}).get("status") != VODPipelineStepStatus.COMPLETED:  # 혹은 Enum 비교
                    missing_steps.append(step)

            if missing_steps:
                raise ValueError(f"[Verify Fail] Incomplete steps for VOD {vod_id}: {missing_steps}")

    async def _upload_to_cloud(self, vod_id: int) -> None:  # 반환 타입 수정 (bool -> None)
        # 로컬 경로 확보
        local_web_dir = self.tmp_storage.get_absolute_path(StoragePaths.get_web_dir(vod_id))

        if not os.path.exists(local_web_dir):
            raise FileNotFoundError(f"Local web directory not found: {local_web_dir}")

        # 리모트 경로 확보
        remote_prefix = BucketPaths.get_vod_prefix(vod_id)

        # 업로드 수행
        await self.cloud_storage.upload_directory(local_web_dir, remote_prefix)

    async def finalize_vod(self, vod_id: int) -> None:
        logger.info(f"[Finalize] Starting finalization for VOD {vod_id}...")

        try:
            # 1. 검증
            await self._evaluate_vod(vod_id)

            # 2. 업로드
            await self._upload_to_cloud(vod_id)

            # 3. 로컬 정리
            await self.tmp_storage.cleanup_vod_directory(vod_id)

            # 4. DB 상태 업데이트
            async with self.db_session_factory() as session:
                async with session.begin():
                    await self.vod_repo.update_vod_pipeline_status(session, vod_id, VODPipelineStatus.COMPLETED)

            logger.info(f"[Finalize] VOD {vod_id} successfully finalized.")

        except Exception as e:
            # 로그에 에러를 남기고 다시 상위로 던져서 API 응답이나 Worker 처리에 알림
            logger.error(f"[Finalize Error] VOD {vod_id} failed: {str(e)}")
            raise e
