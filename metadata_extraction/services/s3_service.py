from typing import BinaryIO
from uuid import UUID
from django.conf import settings
import boto3
from botocore.exceptions import ClientError


class S3Service:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            cls._instance._bucket = settings.AWS_S3_BUCKET_NAME
        return cls._instance

    def upload_file(self, file: BinaryIO, file_id: UUID, original_filename: str, content_type: str) -> str:
        extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
        s3_key = f"uploads/{file_id}.{extension}" if extension else f"uploads/{file_id}"

        self._client.upload_fileobj(
            file,
            self._bucket,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        return s3_key

    def delete_file(self, s3_key: str) -> bool:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            return True
        except ClientError:
            return False

    def get_file_url(self, s3_key: str, expiration: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=expiration,
        )

    @property
    def bucket_name(self) -> str:
        return self._bucket

