"""Cloudflare R2 object storage helper.

Uses S3-compatible API via boto3. All env vars are optional; if not fully
configured the helper becomes a no-op and callers should gracefully continue
storing data in Redis only.

Env vars expected:
  R2_ACCOUNT_ID              (e.g. 123abc456def78901234567890123456)
  R2_ACCESS_KEY_ID
  R2_SECRET_ACCESS_KEY
  R2_BUCKET                  (target bucket name)
  R2_PUBLIC_BASE_URL         (optional: https://cdn.example.com OR https://pub-<hash>.r2.dev)
  R2_BUCKET_PREFIX           (optional key prefix, e.g. artifacts/)

Returned URL precedence:
  If R2_PUBLIC_BASE_URL set -> f"{R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"
  else fallback to native endpoint: https://<account_id>.r2.cloudflarestorage.com/<bucket>/<key>
"""

from __future__ import annotations

import os
import mimetypes
import datetime
from typing import Optional

import boto3  # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from app.utils import create_simple_logger

logger = create_simple_logger(__name__)


class CloudflareR2Storage:
    def __init__(self) -> None:
        self.account_id = os.environ.get("R2_ACCOUNT_ID")
        self.access_key = os.environ.get("R2_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        self.bucket = os.environ.get("R2_BUCKET")
        self.public_base = os.environ.get("R2_PUBLIC_BASE_URL")
        self.prefix = os.environ.get("R2_BUCKET_PREFIX", "")
        self._client = None

        if self.is_configured and boto3 is None:
            logger.warning(
                "Cloudflare R2 env vars present but boto3 not installed. Run 'pip install boto3'."
            )

    @property
    def is_configured(self) -> bool:
        return all([self.account_id, self.access_key, self.secret_key, self.bucket])

    @property
    def client(self):  # lazy init
        if self._client is None and self.is_configured and boto3 is not None:
            endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name="auto",
            )
        return self._client

    def _build_key(self, key: str) -> str:
        if self.prefix:
            return f"{self.prefix.rstrip('/')}/{key.lstrip('/')}"
        return key

    def _guess_content_type(self, key: str, provided: Optional[str]) -> str:
        if provided:
            return provided
        ctype, _ = mimetypes.guess_type(key)
        return ctype or "application/octet-stream"

    def upload_bytes(
        self, data: bytes, *, key: str, content_type: Optional[str] = None
    ) -> Optional[str]:
        """Upload raw bytes to R2. Returns public URL or None on failure/disabled."""
        if not self.is_configured:
            return None
        if not self.client:
            return None
        object_key = self._build_key(key)
        ct = self._guess_content_type(object_key, content_type)
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=data,
                ContentType=ct,
            )
        except (BotoCoreError, ClientError) as e:  # pragma: no cover
            logger.error(f"Failed to upload to R2 key={object_key}: {e}")
            return None

        if self.public_base:
            return f"{self.public_base.rstrip('/')}/{object_key}"
        return f"https://{self.account_id}.r2.cloudflarestorage.com/{self.bucket}/{object_key}"

    def upload_text(
        self, text: str, *, key: str, content_type: str = "text/plain; charset=utf-8"
    ) -> Optional[str]:
        return self.upload_bytes(
            text.encode("utf-8"), key=key, content_type=content_type
        )


r2_storage = CloudflareR2Storage()


def build_artifact_object_key(
    artifact_id: str, *, session_id: Optional[str] = None, extension: str = ""
) -> str:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    base = f"artifacts/{ts}/"
    if session_id:
        base += f"{session_id}/"
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    return f"{base}{artifact_id}{extension}"
