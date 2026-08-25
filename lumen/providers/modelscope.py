"""ModelScope API-Inference through its OpenAI-compatible chat boundary."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from lumen.providers.base import (
    JsonObject,
    MessageContent,
    ProviderResponseError,
    ProviderTransportError,
    normalize_base_url,
    parse_json_object,
    resolve_api_key,
)

MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"


def _openai_client_factory(*, api_key: str, base_url: str) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=api_key, base_url=base_url)


class ModelScopeProvider:
    """One request, one credential resolution; no global client or global key state."""

    provider_name = "modelscope"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._configured_key = api_key
        self.base_url = normalize_base_url(
            base_url or os.getenv("MODELSCOPE_BASE_URL", MODELSCOPE_BASE_URL)
        )
        self._client_factory = client_factory or _openai_client_factory

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        api_key: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra_body: Mapping[str, Any] | None = None,
    ) -> str:
        key = resolve_api_key(
            api_key,
            self._configured_key,
            env_name="MODELSCOPE_API_KEY",
            provider=self.provider_name,
        )
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
            "stream": False,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if extra_body:
            kwargs["extra_body"] = dict(extra_body)
        try:
            client = self._client_factory(api_key=key, base_url=self.base_url)
            response = client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise ProviderTransportError(
                exc,
                provider=self.provider_name,
                operation="chat completion",
                retryable=True,
                secrets=(key,),
            ) from None

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError):
            content = None
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(
                "chat response is missing final content",
                provider=self.provider_name,
                operation="chat completion",
                secrets=(key,),
            )
        return content

    def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: MessageContent,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        max_attempts: int = 2,
        validator: Callable[[JsonObject], Any] | None = None,
        extra_body: Mapping[str, Any] | None = None,
    ) -> JsonObject:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": f"{system.rstrip()}\n\n只返回一个合法 JSON 对象，不要 Markdown 代码块。",
            },
            {"role": "user", "content": user},
        ]
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            raw = self.chat(
                model=model,
                messages=messages,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body=extra_body,
            )
            try:
                parsed = parse_json_object(raw)
                if validator is not None:
                    validator(parsed)
                return parsed
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                if attempt + 1 >= max_attempts:
                    break
                messages.extend(
                    [
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": (
                                "上一个响应不是符合契约的 JSON 对象。请修正并且只返回 JSON 对象。"
                            ),
                        },
                    ]
                )
        raise ProviderResponseError(
            f"model failed strict JSON validation after {max_attempts} attempts: "
            f"{type(last_error).__name__ if last_error else 'unknown error'}",
            provider=self.provider_name,
            operation="strict JSON completion",
        )

    def vision_json(
        self,
        *,
        model: str,
        system: str,
        text: str,
        image_data_urls: Sequence[str],
        api_key: str | None = None,
        **kwargs: Any,
    ) -> JsonObject:
        if not image_data_urls:
            raise ValueError("vision_json requires at least one image")
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        content.extend(
            {
                "type": "image_url",
                "image_url": {"url": image_data_url},
            }
            for image_data_url in image_data_urls
        )
        return self.chat_json(
            model=model,
            system=system,
            user=content,
            api_key=api_key,
            **kwargs,
        )
