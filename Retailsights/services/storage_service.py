"""Storage adapter: S3 uploader and Local fallback.

Usage: call `Storage.upload_bytes(bytes, filename)` which returns a dict with
`{'url': <signed-url-or-local-path>, 'provider': 's3'|'local'}`

Environment variables for S3:
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET
"""
from __future__ import annotations

import os
from typing import Dict


class Storage:
    @staticmethod
    def upload_bytes(data: bytes, filename: str) -> Dict[str, str]:
        """Upload bytes using available backend. Tries S3 first, falls back to local file."""
        # Try S3 if boto3 available and env configured
        try:
            import boto3
            from botocore.exceptions import BotoCoreError
        except Exception:
            boto3 = None

        s3_bucket = os.environ.get("S3_BUCKET")
        if boto3 and s3_bucket:
            try:
                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.environ.get("AWS_REGION"),
                )
                key = f"retailsight/exports/{filename}"
                s3.put_object(Bucket=s3_bucket, Key=key, Body=data)
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": s3_bucket, "Key": key},
                    ExpiresIn=3600,
                )
                return {"url": url, "provider": "s3"}
            except Exception:
                # fallthrough to local
                pass

        # Local fallback
        export_dir = os.environ.get("EXPORT_DIR", "exports")
        os.makedirs(export_dir, exist_ok=True)
        path = os.path.join(export_dir, filename)
        with open(path, "wb") as f:
            f.write(data)

        # Return file:// path for convenience
        return {"url": f"file://{os.path.abspath(path)}", "provider": "local"}
