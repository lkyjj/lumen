"""Typed, secret-safe boundaries shared by all external model providers."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, TypeAlias, runtime_checkable

from lumen.runlog import redact

JsonObject: TypeAlias = dict[str, Any]
MessageContent: TypeAlias = str | list[dict[str, Any]]

_DATA_URL = re.compile(
    r"data:[A-Za-z0-9.+-]+/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/=_-]+",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)(authorization\s*[:=]?\s*bearer\s+)[^\s,;]+")
_SIGNED_QUERY = re.compile(r"(?i)([?&](?:signature|x-oss-signature|token)=)[^&\s]+")
_SIGNED_URL = re.compile(r"https?://[^\s?]+\?[^\s]+", re.IGNORECASE)


def sanitize_text(value: object, *, secrets: Sequence[str] = ()) -> str:
    """Return a useful diagnostic without credentials, auth headers, or media blobs."""

    text = str(value)
    for secret in sorted((item for item in secrets if item), key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    text = _DATA_URL.sub("[REDACTED_DATA_URL]", text)
    text = _BEARER.sub(r"\1[REDACTED]", text)
    text = _SIGNED_URL.sub("[REDACTED_SIGNED_URL]", text)
    text = _SIGNED_QUERY.sub(r"\1[REDACTED]", text)
    return str(redact(text))


class ProviderError(RuntimeError):
    """Base error containing only safe, structured provider context."""

    def __init__(
        self,
        message: object,
        *,
        provider: str,
        operation: str,
        code: str | None = None,
        status_code: int | None = None,
        retryable: bool = False,
        secrets: Sequence[str] = (),
    ) -> None:
        self.provider = provider
        self.operation = operation
        self.code = sanitize_text(code, secrets=secrets) if code else None
        self.status_code = status_code
        self.retryable = retryable
        safe_message = sanitize_text(message, secrets=secrets)
        context = [provider, operation]
        if status_code is not None:
            context.append(f"HTTP {status_code}")
        if self.code:
            context.append(self.code)
        super().__init__(f"{' / '.join(context)}: {safe_message}")


class ProviderAuthError(ProviderError):
    """Raised before a request when no usable provider credential exists."""


class ProviderTransportError(ProviderError):
    """Raised for network and HTTP-layer failures."""


class ProviderResponseError(ProviderError):
    """Raised when a successful response violates the documented schema."""


class ProviderTimeoutError(ProviderError):
    """Raised when a finite asynchronous poll deadline expires."""


class UnsupportedModelError(ProviderError):
    """Raised when a model has no verified payload capability definition."""


@runtime_checkable
class BudgetLike(Protocol):
    def check(self, amount: float, *, note: str = "") -> None: ...

    def charge(
        self,
        amount: float,
        *,
        agent: str,
        model: str,
        note: str = "",
        details: dict[str, Any] | None = None,
        reserved: bool = False,
    ) -> None: ...


@runtime_checkable
class HTTPSession(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...


@runtime_checkable
class LLMProvider(Protocol):
    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        api_key: str | None = None,
        **kwargs: Any,
    ) -> str: ...

    def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: MessageContent,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> JsonObject: ...


@runtime_checkable
class VLMProvider(Protocol):
    def vision_json(
        self,
        *,
        model: str,
        system: str,
        text: str,
        image_data_urls: Sequence[str],
        api_key: str | None = None,
        **kwargs: Any,
    ) -> JsonObject: ...


@dataclass(frozen=True)
class ImageResult:
    path: Path
    model: str
    cost_cny: float
    request_id: str | None = None


@dataclass(frozen=True)
class VideoResult:
    path: Path
    model: str
    task_id: str
    cost_cny: float
    request_id: str | None = None
    usage: JsonObject = field(default_factory=dict)


@dataclass(frozen=True)
class AudioResult:
    path: Path
    model: str
    cost_cny: float
    request_id: str | None = None


@runtime_checkable
class ImageProvider(Protocol):
    def generate(self, prompt: str, output_path: str | Path, **kwargs: Any) -> ImageResult: ...


@runtime_checkable
class VideoProvider(Protocol):
    def generate_from_image(
        self,
        prompt: str,
        image_path: str | Path,
        output_path: str | Path,
        **kwargs: Any,
    ) -> VideoResult: ...


@runtime_checkable
class TTSProvider(Protocol):
    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        **kwargs: Any,
    ) -> AudioResult: ...


def resolve_api_key(
    request_key: str | None,
    configured_key: str | None,
    *,
    env_name: str,
    provider: str,
) -> str:
    """Resolve request > constructor > environment without retaining it in errors."""

    for candidate in (request_key, configured_key, os.getenv(env_name)):
        if candidate and candidate.strip():
            return candidate.strip()
    raise ProviderAuthError(
        f"missing {env_name}",
        provider=provider,
        operation="authenticate",
    )


def normalize_base_url(value: str) -> str:
    return value.rstrip("/")


def parse_json_object(text: str) -> JsonObject:
    """Parse one strict JSON object, tolerating only common transport wrappers."""

    value = text.strip()
    if "</think>" in value:
        value = value.rsplit("</think>", maxsplit=1)[-1].strip()
    if value.startswith("```"):
        first_newline = value.find("\n")
        if first_newline != -1 and value.endswith("```"):
            value = value[first_newline + 1 : -3].strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise TypeError("model response must be a JSON object")
    return parsed


def response_message(payload: object) -> tuple[str | None, str]:
    """Extract only documented error code/message fields from a response body."""

    if not isinstance(payload, dict):
        return None, "provider returned an error"
    output = payload.get("output")
    candidates = [output, payload] if isinstance(output, dict) else [payload]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        code = candidate.get("code")
        message = candidate.get("message")
        if code is not None or message is not None:
            return (
                str(code) if code is not None else None,
                str(message) if message is not None else "provider returned an error",
            )
    return None, "provider returned an error"


def request_json(
    session: HTTPSession,
    method: str,
    url: str,
    *,
    provider: str,
    operation: str,
    api_key: str,
    timeout: float,
    headers: Mapping[str, str] | None = None,
    payload: JsonObject | None = None,
) -> JsonObject:
    """Make one JSON request while keeping request headers and bodies out of errors."""

    try:
        response = session.request(
            method,
            url,
            headers=dict(headers or {}),
            json=payload,
            timeout=timeout,
        )
    except Exception as exc:
        raise ProviderTransportError(
            exc,
            provider=provider,
            operation=operation,
            retryable=True,
            secrets=(api_key,),
        ) from None

    status_code = int(getattr(response, "status_code", 0) or 0)
    try:
        body = response.json()
    except Exception:
        body = None
    if not 200 <= status_code < 300:
        code, message = response_message(body)
        retryable = status_code in {408, 409, 425, 429} or status_code >= 500
        raise ProviderTransportError(
            message,
            provider=provider,
            operation=operation,
            code=code,
            status_code=status_code,
            retryable=retryable,
            secrets=(api_key,),
        )
    if not isinstance(body, dict):
        raise ProviderResponseError(
            "response body is not a JSON object",
            provider=provider,
            operation=operation,
            status_code=status_code,
            secrets=(api_key,),
        )
    return body


def download_bytes(
    session: HTTPSession,
    url: str,
    *,
    provider: str,
    operation: str,
    api_key: str,
    timeout: float,
    max_bytes: int,
) -> bytes:
    """Download a short-lived result without exposing its signed URL in failures."""

    try:
        response = session.request("GET", url, timeout=timeout, stream=True)
    except Exception as exc:
        raise ProviderTransportError(
            exc,
            provider=provider,
            operation=operation,
            retryable=True,
            secrets=(api_key,),
        ) from None
    status_code = int(getattr(response, "status_code", 0) or 0)
    if not 200 <= status_code < 300:
        raise ProviderTransportError(
            "result download failed",
            provider=provider,
            operation=operation,
            status_code=status_code,
            retryable=status_code == 429 or status_code >= 500,
            secrets=(api_key,),
        )

    chunks: list[bytes] = []
    size = 0
    iterator = getattr(response, "iter_content", None)
    if callable(iterator):
        source = iterator(chunk_size=64 * 1024)
    else:
        source = [getattr(response, "content", b"")]
    try:
        for chunk in source:
            if not chunk:
                continue
            data = bytes(chunk)
            size += len(data)
            if size > max_bytes:
                raise ProviderResponseError(
                    f"download exceeds {max_bytes} bytes",
                    provider=provider,
                    operation=operation,
                    secrets=(api_key,),
                )
            chunks.append(data)
    except ProviderError:
        raise
    except Exception as exc:
        raise ProviderTransportError(
            exc,
            provider=provider,
            operation=operation,
            retryable=True,
            secrets=(api_key,),
        ) from None
    return b"".join(chunks)


def atomic_write(path: str | Path, data: bytes) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.part")
    temporary.write_bytes(data)
    temporary.replace(target)
    return target


def find_nested_string(payload: object, keys: Sequence[str]) -> str | None:
    """Find a documented string field without logging or returning its container."""

    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        for value in payload.values():
            found = find_nested_string(value, keys)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_nested_string(value, keys)
            if found:
                return found
    return None


def request_id(payload: JsonObject) -> str | None:
    value = payload.get("request_id")
    return str(value) if value else None


def default_requests_session() -> HTTPSession:
    import requests

    return requests.Session()
