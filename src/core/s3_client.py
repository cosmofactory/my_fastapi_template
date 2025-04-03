import io
import logging
import uuid

import aioboto3
import httpx
import logfire
from aiobotocore.config import AioConfig

from src.settings import settings


class S3Client:
    """
    An asynchronous client for interacting with DigitalOcean Spaces using S3‑compatible APIs.

    Parameters:
        access_key (str): Your DigitalOcean Spaces access key.
        secret_key (str): Your DigitalOcean Spaces secret access key.
        endpoint_url (str): The Spaces endpoint URL.
    """

    def __init__(self, http_client: httpx.AsyncClient):
        self.access_key = settings.s3.ACCESS_KEY
        self.secret_key = settings.s3.SECRET_KEY
        self.endpoint_url = settings.s3.ENDPOINT_URL
        self.region = settings.s3.REGION
        self.session = aioboto3.Session()
        self.http_client = http_client
        self.bucket_name = settings.s3.BUCKET_NAME

    @logfire.instrument()
    async def upload_file_from_url(self, file_url: str) -> str:
        """
        Downloads a file from a URL and uploads it to the specified bucket and key.

        Args:
            bucket (str): The bucket (Space) name.
            key (str): The target object key (file name/path in the bucket).
            file_url (str): URL of the file to download.

        Returns:
            str: s3 file key.
        """
        try:
            response = await self.http_client.get(file_url)
            response.raise_for_status()
            file_bytes = io.BytesIO(response.content)
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3_client:
                file_id = str(uuid.uuid4())
                await s3_client.upload_fileobj(file_bytes, self.bucket_name, file_id)
            return file_id
        except Exception as e:
            logfire.error(
                f"Error uploading file from {file_url}: {e}",
                error=e,
            )
            raise e

    @logfire.instrument()
    async def fetch_file(self, key: str) -> bytes:
        """
        Fetches a file from the specified bucket and key.

        Args:
            bucket (str): The bucket (Space) name.
            key (str): The object key.

        Returns:
            bytes: The content of the file, or empty bytes on failure.
        """
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3_client:
                response = await s3_client.get_object(Bucket=self.bucket_name, Key=key)
                data = await response["Body"].read()
            return data
        except Exception as e:
            logfire.error(f"Error fetching file {self.bucket_name}/{key}: {e}", error=e)
            raise e

    @logfire.instrument()
    async def list_files(self, bucket: str, prefix: str = "") -> list:
        """
        Lists all files in the specified bucket that match an optional prefix.

        Args:
            bucket (str): The bucket (Space) name.
            prefix (str): Filter to list keys starting with this prefix.

        Returns:
            list: A list of object keys.
        """
        keys = []
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3_client:
                paginator = s3_client.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    if "Contents" in page:
                        keys.extend([obj["Key"] for obj in page["Contents"]])
            return keys
        except Exception as e:
            logging.error(f"Error listing files in {bucket} with prefix '{prefix}': {e}")
            return []

    @logfire.instrument()
    async def delete_file(self, bucket: str, key: str) -> bool:
        """
        Deletes the specified file from the bucket.

        Args:
            bucket (str): The bucket (Space) name.
            key (str): The object key to delete.

        Returns:
            bool: True if deletion was successful; False otherwise.
        """
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3_client:
                await s3_client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logging.error(f"Error deleting file {bucket}/{key}: {e}")
            return False

    async def get_file_metadata(self, bucket: str, key: str) -> dict:
        """
        Retrieves metadata for a specified file in the bucket.

        Args:
            bucket (str): The bucket (Space) name.
            key (str): The object key.

        Returns:
            dict: The file's metadata, or an empty dict on failure.
        """
        try:
            async with self.session.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as s3_client:
                response = await s3_client.head_object(Bucket=bucket, Key=key)
            return response
        except Exception as e:
            logging.error(f"Error fetching metadata for {bucket}/{key}: {e}")
            return {}

    @logfire.instrument(record_return=True)
    async def generate_presigned_url(
        self, key: str, expires_in: int = settings.s3.URL_EXPIRATION_SECONDS
    ) -> str:
        """
        Generates a presigned URL to allow direct download of the file.

        Adjust file to fit the default file extension.
        Args:
            key (str): The object key.
            expires_in (int): Lifetime of the URL in seconds.

        Returns:
            str: A presigned URL.
        """
        filename = (
            key
            if key.endswith(settings.minimax.DEFAULT_FILE_EXTENSION)
            else f"{key} + {settings.minimax.DEFAULT_FILE_EXTENSION}"
        )
        async with self.session.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=AioConfig(signature_version="s3v4"),
        ) as s3_client:
            url = await s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    "ResponseContentDisposition": f"attachment; filename={filename}",
                    "ResponseContentType": settings.minimax.DEFAULT_VIDEO_CONTENT_TYPE,
                },
                ExpiresIn=expires_in,
            )
        return url
