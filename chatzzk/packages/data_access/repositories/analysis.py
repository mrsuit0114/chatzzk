from loguru import logger
from sqlalchemy.orm import Session

from chatzzk.packages.schemas.db_models import ChzzkAnalysisResultORM, ChzzkVodORM


class AnalysisResultRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, vod: ChzzkVodORM, result_data: dict) -> ChzzkAnalysisResultORM:
        """최종 결과물 정보를 DB에 생성합니다."""
        try:
            db_result = ChzzkAnalysisResultORM(vod_pk=vod.id, **result_data)
            self.db.add(db_result)
            self.db.commit()
            self.db.refresh(db_result)
            logger.success(f"✅ Created analysis result for video_no: {vod.video_no}")
            return db_result
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to create analysis result for video_no {vod.video_no}: {e}")
            raise
