from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import cast

from chatzzk_data_access.orm.models import VOD, VODPipelineLog


class VODRepository:
    async def bulk_insert_if_not_exists(self, session: AsyncSession, vod_dicts: list[dict]) -> list[int]:
        if not vod_dicts:
            return []

        # values()에 dict 리스트 전달
        stmt = pg_insert(VOD).values(vod_dicts)

        stmt = stmt.on_conflict_do_nothing(index_elements=["channel_id", "video_no"])

        stmt = stmt.returning(VOD.id)

        result = await session.execute(stmt)
        return result.scalars().all()

    # [NEW] 로그 생성 메서드 추가
    async def bulk_insert_logs(self, session: AsyncSession, log_dicts: list[dict]) -> None:
        """
        신규 VOD들에 대한 초기 PipelineLog를 생성합니다.
        log_dicts 구조: [{'vod_id': 1}, {'vod_id': 2}, ...]
        """
        if not log_dicts:
            return

        # 단순 Insert (Log는 충돌 날 일이 없으므로 기본 insert 사용 가능하나,
        # 통일성을 위해 pg_insert 사용 혹은 core insert 사용)
        stmt = pg_insert(VODPipelineLog).values(log_dicts)

        # 로그는 RETURNING 필요 없음
        await session.execute(stmt)

    async def get_log_details(self, session: AsyncSession, vod_id: int) -> dict:
        stmt = select(VODPipelineLog.process_details).where(VODPipelineLog.vod_id == vod_id)
        result = await session.execute(stmt)
        details = result.scalar_one_or_none()

        return details if details is not None else {}

    async def update_log_details(self, session: AsyncSession, vod_id: int, update_payload: dict) -> None:
        stmt = (
            update(VODPipelineLog)
            .where(VODPipelineLog.vod_id == vod_id)
            .values(process_details=VODPipelineLog.process_details.op("||")(cast(update_payload, JSONB)))
        )
        await session.execute(stmt)
