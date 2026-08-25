"""Shared HTTP mechanics for Alibaba Cloud Model Studio native APIs."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable

from lumen.providers.base import (
    BudgetLike,
    HTTPSession,
    JsonObject,
    ProviderResponseError,
    ProviderTimeoutError,
    default_requests_session,
    find_nested_string,
    normalize_base_url,
    request_json,
    resolve_api_key,
)

DASHSCOPE_LEGACY_NATIVE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")


def default_native_base_url() -> str:
    explicit = os.getenv("DASHSCOPE_NATIVE_BASE_URL")
    if explicit:
        return normalize_base_url(explicit)
    workspace_id = os.getenv("DASHSCOPE_WORKSPACE_ID")
    if workspace_id:
        return f"https://{workspace_id}.cn-beijing.maas.aliyuncs.com/api/v1"
    return DASHSCOPE_LEGACY_NATIVE_BASE_URL


class DashScopeHTTPProvider:
    provider_name = "dashscope"

    def __init__(
        self,
        *,
        budget: BudgetLike,
        api_key: str | None = None,
        base_url: str | None = None,
        session: HTTPSession | None = None,
        request_timeout: float = 30,
        download_timeout: float = 120,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if request_timeout <= 0 or download_timeout <= 0:
            raise ValueError("timeouts must be positive")
        self.budget = budget
        self._configured_key = api_key
        self.base_url = normalize_base_url(base_url or default_native_base_url())
        self.session = session or default_requests_session()
        self.request_timeout = request_timeout
        self.download_timeout = download_timeout
        self._sleep = sleeper
        self._clock = clock

    def _api_key(self, request_key: str | None) -> str:
        return resolve_api_key(
            request_key,
            self._configured_key,
            env_name="DASHSCOPE_API_KEY",
            provider=self.provider_name,
        )

    @staticmethod
    def _headers(api_key: str, *, asynchronous: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if asynchronous:
            headers["X-DashScope-Async"] = "enable"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        api_key: str,
        operation: str,
        payload: JsonObject | None = None,
        asynchronous: bool = False,
    ) -> JsonObject:
        return request_json(
            self.session,
            method,
            f"{self.base_url}/{path.lstrip('/')}",
            provider=self.provider_name,
            operation=operation,
            api_key=api_key,
            timeout=self.request_timeout,
            headers=self._headers(api_key, asynchronous=asynchronous),
            payload=payload,
        )

    def _poll_task(
        self,
        task_id: str,
        *,
        api_key: str,
        poll_interval: float,
        poll_timeout: float,
    ) -> JsonObject:
        if not _TASK_ID.fullmatch(task_id):
            raise ProviderResponseError(
                "provider returned an invalid task id",
                provider=self.provider_name,
                operation="poll async task",
            )
        if poll_interval <= 0 or poll_timeout <= 0:
            raise ValueError("poll interval and timeout must be positive")
        deadline = self._clock() + poll_timeout
        first_poll = True
        while True:
            if not first_poll and self._clock() >= deadline:
                raise ProviderTimeoutError(
                    "async task did not finish before deadline",
                    provider=self.provider_name,
                    operation="poll async task",
                    retryable=True,
                )
            first_poll = False
            payload = self._request(
                "GET",
                f"tasks/{task_id}",
                api_key=api_key,
                operation="poll async task",
            )
            output = payload.get("output")
            if not isinstance(output, dict):
                raise ProviderResponseError(
                    "task response is missing output",
                    provider=self.provider_name,
                    operation="poll async task",
                )
            status = str(output.get("task_status", "")).upper()
            if status == "SUCCEEDED":
                return payload
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                code = output.get("code")
                message = output.get("message") or f"async task ended with {status}"
                raise ProviderResponseError(
                    message,
                    provider=self.provider_name,
                    operation="poll async task",
                    code=str(code) if code else status,
                    secrets=(api_key,),
                )
            if status not in {"PENDING", "RUNNING"}:
                raise ProviderResponseError(
                    f"unknown task status: {status or 'missing'}",
                    provider=self.provider_name,
                    operation="poll async task",
                )
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise ProviderTimeoutError(
                    "async task did not finish before deadline",
                    provider=self.provider_name,
                    operation="poll async task",
                    retryable=True,
                )
            self._sleep(min(poll_interval, remaining))

    @staticmethod
    def _task_id(payload: JsonObject) -> str:
        task_id = find_nested_string(payload, ("task_id",))
        if not task_id:
            raise ProviderResponseError(
                "task creation response is missing task_id",
                provider="dashscope",
                operation="create async task",
            )
        return task_id

    @staticmethod
    def _usage(payload: JsonObject) -> JsonObject:
        usage = payload.get("usage")
        return dict(usage) if isinstance(usage, dict) else {}
