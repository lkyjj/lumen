"""Paid DashScope text-to-image provider with budget enforcement."""

from __future__ import annotations

from pathlib import Path

from lumen.providers.base import (
    ImageResult,
    ProviderResponseError,
    download_bytes,
    find_nested_string,
    request_id,
)
from lumen.providers.dashscope import DashScopeHTTPProvider
from lumen.providers.media import MAX_IMAGE_BYTES, save_rgb_image


class DashScopeT2IProvider(DashScopeHTTPProvider):
    """Wan2.6 T2I synchronous API used for final character anchors."""

    endpoint = "services/aigc/multimodal-generation/generation"

    def __init__(
        self,
        *,
        model: str = "wan2.6-t2i",
        price_cny_each: float = 0.20,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        if price_cny_each < 0:
            raise ValueError("price_cny_each must be non-negative")
        self.model = model
        self.price_cny_each = float(price_cny_each)

    def generate(
        self,
        prompt: str,
        output_path: str | Path,
        *,
        size: str = "1696*960",
        negative_prompt: str = "",
        prompt_extend: bool = True,
        watermark: bool = False,
        api_key: str | None = None,
    ) -> ImageResult:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        cost = round(self.price_cny_each, 2)
        note = "generate one anchor image"
        self.budget.check(cost, note=note)
        key = self._api_key(api_key)
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": 1,
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
            },
        }
        response = self._request(
            "POST",
            self.endpoint,
            api_key=key,
            operation="generate image",
            payload=payload,
        )
        image_url = find_nested_string(response, ("image", "image_url", "url"))
        if not image_url:
            raise ProviderResponseError(
                "image response is missing an output URL",
                provider=self.provider_name,
                operation="generate image",
            )
        response_id = request_id(response)
        self.budget.charge(
            cost,
            agent="art_director",
            model=self.model,
            note=note,
            details={"request_id": response_id, "count": 1, "size": size},
        )
        raw = download_bytes(
            self.session,
            image_url,
            provider=self.provider_name,
            operation="download image",
            api_key=key,
            timeout=self.download_timeout,
            max_bytes=MAX_IMAGE_BYTES,
        )
        path = save_rgb_image(raw, output_path, provider=self.provider_name)
        return ImageResult(path=path, model=self.model, cost_cny=cost, request_id=response_id)
