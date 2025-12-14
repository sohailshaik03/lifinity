from __future__ import annotations

import io
import os
from .celery_app import celery_app
from .analytics_service import AnalyticsService
from .storage_service import Storage
from ..repositories.exports_repo import create_export, update_export
import pandas as pd
import time
from ..logger import logger
from typing import Optional


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, retry_kwargs={"max_retries": 3})
def generate_and_upload_report(self, csv_bytes: bytes, filename_prefix: str = "report", shop_id: Optional[int] = None, user_id: Optional[int] = None) -> dict:
    """Task: create PDF from CSV bytes and upload to storage, returning the URL.

    This task writes a record in `report_exports` (pending -> completed/failed).
    """
    task_id = self.request.id

    # record export metadata
    export_id = create_export(shop_id=shop_id, user_id=user_id, filename=f"{filename_prefix}.pdf", task_id=task_id, status="pending")

    try:
        # recreate DataFrame
        df = pd.read_csv(io.BytesIO(csv_bytes))
        df = AnalyticsService.normalize(df)
        df = AnalyticsService.preprocess(df)

        pdf_bytes = AnalyticsService.export_pdf_bytes(df)

        fname = f"{filename_prefix}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        result = Storage.upload_bytes(pdf_bytes, fname)

        # update DB record
        update_export(export_id, provider=result.get("provider"), url=result.get("url"), status="completed", completed_at=pd.Timestamp.now())
        logger.info("Report task completed: %s -> %s", export_id, result.get("url"))
        return result

    except Exception as e:
        logger.exception("Report generation failed for task %s", task_id)
        # mark as failed
        try:
            update_export(export_id, status="failed", completed_at=pd.Timestamp.now())
        except Exception:
            logger.exception("Failed to update export record for failed task %s", task_id)
        # re-raise to trigger retry if configured
        raise
