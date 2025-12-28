import asyncio
import mimetypes
import os

from aiobotocore.session import AioSession
from botocore.errorfactory import ClientError
from loguru import logger

from chatzzk_data_access.storages import BaseCloudStorage


class R2Storage(BaseCloudStorage):
    def __init__(
        self,
        session: AioSession,
        account_id: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        public_domain: str | None = None,
    ):
        """
        :param account_id: Cloudflare Account ID
        :param access_key: R2 Access Key ID
        :param secret_key: R2 Secret Access Key
        :param bucket_name: R2 Bucket Name
        :param public_domain: (Optional) 웹 접근을 위한 커스텀 도메인 또는 r2.dev 주소
        """
        self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.public_domain = public_domain

        # [세션 관리] 세션 객체는 가벼우므로 인스턴스 변수로 유지합니다.
        self.session = session

    async def _upload_file(self, local_path: str, remote_key: str, content_type: str = None) -> str:
        # Content-Type 자동 추론 (웹 서빙 시 필수)
        if content_type is None:
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type is None:
                content_type = "application/octet-stream"  # 기본값

        # [클라이언트 관리] 사용할 때 생성하고, 블록을 나가면 자동으로 닫힙니다.
        async with self.session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",  # R2는 리전 구분이 없으므로 auto 사용
        ) as client:
            try:
                with open(local_path, "rb") as f:
                    file_content = f.read()

                await client.put_object(
                    Bucket=self.bucket_name, Key=remote_key, Body=file_content, ContentType=content_type
                )
            except ClientError as e:
                # 로깅을 추가하면 좋습니다.
                logger.error(f"Failed to upload {local_path} to R2: {e}")
                raise e

        # URL 반환 로직
        if self.public_domain:
            # 도메인 끝에 슬래시 처리를 안전하게 수행
            domain = self.public_domain.rstrip("/")
            clean_key = remote_key.lstrip("/")
            return f"{domain}/{clean_key}"

        return remote_key

    async def upload_directory(self, local_dir: str, remote_prefix: str) -> list[str]:
        uploaded_keys = []
        upload_tasks = []

        # os.walk는 동기 함수지만 파일 탐색 자체는 빠르므로 여기서는 그대로 사용합니다.
        # 파일이 매우 많다면 aiofiles.os 등을 고려할 수 있습니다.
        for root, _, files in os.walk(local_dir):
            for file in files:
                local_file_path = os.path.join(root, file)

                # 상대 경로 계산 (예: local_dir/subdir/file.json -> subdir/file.json)
                relative_path = os.path.relpath(local_file_path, local_dir)

                # 원격 키 생성 (Windows의 백슬래시를 슬래시로 변환)
                remote_object_key = os.path.join(remote_prefix, relative_path).replace("\\", "/")

                # Task 생성
                task = self._upload_file(local_file_path, remote_object_key)
                upload_tasks.append(task)

        # 병렬 업로드 실행
        if upload_tasks:
            # return_exceptions=False로 설정하여 하나라도 실패하면 에러를 띄우도록 함
            results = await asyncio.gather(*upload_tasks)
            uploaded_keys.extend(results)

        return uploaded_keys
