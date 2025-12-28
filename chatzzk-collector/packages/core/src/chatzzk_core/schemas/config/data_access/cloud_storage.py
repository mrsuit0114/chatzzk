from pydantic import BaseModel


class CloudStorageConfig(BaseModel):
    account_id: str
    access_key: str
    secret_key: str
    bucket_name: str
    public_domain: str | None = None
