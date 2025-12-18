"""
Storage helpers: filesystem and optional S3 (boto3).
"""
import os
from pathlib import Path
from typing import Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # boto3 optional
    boto3 = None
    BotoCoreError = ClientError = Exception


def save_bytes_fs(base_path: Path, relative_path: str, data: bytes) -> Path:
    target = base_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def read_bytes_fs(path: Path) -> Optional[bytes]:
    return path.read_bytes() if path.exists() else None


def save_bytes_s3(bucket: str, key: str, data: bytes) -> bool:
    if boto3 is None:
        raise ImportError("boto3 not installed")
    try:
        client = boto3.client(
            "s3",
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        )
        client.put_object(Bucket=bucket, Key=key, Body=data)
        return True
    except (BotoCoreError, ClientError):
        return False

