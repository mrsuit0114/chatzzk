from loguru import logger

from chatzzk.packages.data_access.storage.base import StorageInterface
from chatzzk.packages.schemas.storage_configs import MinioConfig, StorageConfig


def create_storage_manager(storage_config: StorageConfig) -> StorageInterface:
    impl_name = storage_config.storage_implementation.upper()
    logger.info(f"Creating storage manager for implementation: {impl_name}")

    if isinstance(storage_config, MinioConfig):
        from chatzzk.packages.data_access.storage.minio_storage import MinioStorageManager

        return MinioStorageManager(storage_config)

    else:
        raise TypeError(f"Unsupported storage config type: {type(storage_config)}")
