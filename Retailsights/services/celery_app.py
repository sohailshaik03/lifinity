from __future__ import annotations

import os
import types
from typing import Any, Callable


def _make_stub_celery():
    """Return a lightweight stub object that provides the minimal interface
    used by the app when Celery isn't installed. This keeps the app running
    in environments where Celery isn't available (dev machines without worker).
    """

    class _AsyncResultStub:
        def __init__(self, task_id: str | None = None):
            self._id = task_id or "stub"

        @property
        def id(self):
            return self._id

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

        @property
        def result(self):
            return None

    class _CeleryStub:
        def __init__(self):
            self._tasks = {}

        def task(self, *args, **kwargs):
            # decorator that returns the function unchanged
            def _decorator(func: Callable[..., Any]):
                self._tasks[func.__name__] = func
                return func

            return _decorator

        def AsyncResult(self, task_id: str | None):
            return _AsyncResultStub(task_id)

    return _CeleryStub()


try:
    from celery import Celery  # type: ignore

    def make_celery(app_name: str = "retailsight") -> Celery:
        broker = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
        backend = os.environ.get("CELERY_RESULT_BACKEND") or broker
        celery = Celery(app_name, broker=broker, backend=backend)
        # optional: configure task serialization, timeouts, etc.
        celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
        return celery


    celery_app = make_celery()
except Exception:
    # Celery not installed or failed to initialize — provide a safe stub
    celery_app = _make_stub_celery()  # type: ignore
