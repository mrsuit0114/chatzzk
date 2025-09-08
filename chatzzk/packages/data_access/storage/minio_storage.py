import io

import orjson
from loguru import logger

from chatzzk.packages.constants.service_codes import StorageObject
from chatzzk.packages.data_access.storage.base import StorageInterface
from chatzzk.packages.schemas.data_models import StreamContextEntry
from chatzzk.packages.schemas.storage_configs import MinioConfig
from minio import Minio


class MinioStorageManager(StorageInterface):
    def __init__(self, config: MinioConfig):
        self.bucket_name = config.bucket_name
        logger.info(f"Initializing MinIO client for endpoint '{config.endpoint}' and bucket '{self.bucket_name}'...")

        try:
            self.client = Minio(
                config.endpoint, access_key=config.access_key, secret_key=config.secret_key, secure=config.secure
            )

            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created.")
            else:
                logger.info(f"Bucket '{self.bucket_name}' already exists.")
            logger.success("✅ MinIO client initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO client: {e}")
            raise

    def _get_context_object_name(self, video_no: str) -> str:
        # 파일 경로/키 생성 규칙을 중앙에서 관리
        return StorageObject.VIDEO_CONTEXT.format(video_no=video_no)

    def save_context(self, video_no: str, video_context: list[StreamContextEntry]) -> str:
        if not video_context:
            logger.warning(f"Context data for {video_no} is empty. Skipping save.")
            return ""

        object_name = self._get_context_object_name(video_no)

        # Pydantic 모델 리스트를 jsonl 형식의 바이트 데이터로 변환
        # orjson.dumps는 바이트를 반환하므로 .encode() 필요 없음
        jsonl_content = b"\n".join([orjson.dumps(entry.model_dump()) for entry in video_context])
        data_stream = io.BytesIO(jsonl_content)
        data_len = len(jsonl_content)

        logger.info(f"Uploading {data_len / 1024:.2f} KB of context data to MinIO: {object_name}")

        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                data=data_stream,
                length=data_len,
                content_type="application/x-ndjson",  # jsonl의 표준 MIME 타입
            )
            logger.success(f"✅ Successfully saved context for {video_no} to MinIO.")
            return object_name
        except Exception as e:
            logger.error(f"❌ Failed to save context for {video_no} to MinIO: {e}")
            raise

    def load_context(self, video_no: str) -> list[StreamContextEntry] | None:
        object_name = self._get_context_object_name(video_no)
        logger.info(f"Loading context data from MinIO: {object_name}")

        try:
            with self.client.get_object(self.bucket_name, object_name) as response:
                content_bytes = response.read()

            context_list = []
            for line in content_bytes.strip().split(b"\n"):
                if line:
                    data = orjson.loads(line)
                    context_list.append(StreamContextEntry.model_validate(data))

            logger.success(f"✅ Successfully loaded {len(context_list)} context entries for {video_no}.")
            return context_list

        except Exception as e:
            # MinIO에서 object not found 에러는 S3Error를 발생시킴
            logger.error(f"❌ Failed to load context for {video_no} from MinIO: {e}")
            return None
        finally:
            response.close()
            response.release_conn()
