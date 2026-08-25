"""DashScope CosyVoice non-realtime text-to-speech provider."""

from __future__ import annotations

from pathlib import Path

from lumen.providers.base import (
    AudioResult,
    ProviderResponseError,
    atomic_write,
    download_bytes,
    find_nested_string,
    request_id,
)
from lumen.providers.dashscope import DashScopeHTTPProvider

_AUDIO_FORMATS = {"mp3", "opus", "pcm", "wav"}
_SAMPLE_RATES = {8_000, 16_000, 22_050, 24_000, 44_100, 48_000}
_LANGUAGE_HINTS = {
    "ar",
    "de",
    "en",
    "es",
    "fil",
    "fr",
    "id",
    "it",
    "ja",
    "ko",
    "ms",
    "pt",
    "ru",
    "th",
    "vi",
    "zh",
}


def _instruction_length(value: str) -> int:
    return sum(2 if "\u3400" <= character <= "\u9fff" else 1 for character in value)


class DashScopeTTSProvider(DashScopeHTTPProvider):
    """Generate one audio file through the documented non-realtime endpoint."""

    endpoint = "services/audio/tts/SpeechSynthesizer"
    max_download_bytes = 100 * 1024 * 1024

    def __init__(
        self,
        *,
        model: str = "cosyvoice-v3-flash",
        price_cny_per_10k_chars: float = 1.00,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        if price_cny_per_10k_chars < 0:
            raise ValueError("price_cny_per_10k_chars must be non-negative")
        self.model = model
        self.price_cny_per_10k_chars = float(price_cny_per_10k_chars)

    def estimate_cost(self, text: str) -> float:
        return round(len(text) * self.price_cny_per_10k_chars / 10_000, 2)

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        *,
        voice: str,
        instruction: str | None = None,
        language_hint: str | None = None,
        sample_rate: int = 24_000,
        audio_format: str = "wav",
        api_key: str | None = None,
    ) -> AudioResult:
        if not text.strip():
            raise ValueError("text must not be empty")
        if not voice.strip():
            raise ValueError("voice must not be empty")
        if len(text) > 20_000:
            raise ValueError("text must not exceed 20000 characters")
        if instruction is not None and _instruction_length(instruction) > 100:
            raise ValueError("instruction must not exceed 100 weighted characters")
        if sample_rate not in _SAMPLE_RATES:
            raise ValueError(f"unsupported sample rate: {sample_rate}")
        if audio_format not in _AUDIO_FORMATS:
            raise ValueError(f"unsupported audio format: {audio_format}")
        if language_hint is not None and language_hint not in _LANGUAGE_HINTS:
            raise ValueError(f"unsupported language hint: {language_hint}")

        cost = self.estimate_cost(text)
        note = f"synthesize {len(text)} characters"
        self.budget.check(cost, note=note)
        key = self._api_key(api_key)

        input_: dict[str, object] = {
            "text": text,
            "voice": voice,
            "format": audio_format,
            "sample_rate": sample_rate,
        }
        if instruction:
            input_["instruction"] = instruction
        if language_hint:
            input_["language_hints"] = [language_hint]
        payload = {"model": self.model, "input": input_}
        response = self._request(
            "POST",
            self.endpoint,
            api_key=key,
            operation="synthesize speech",
            payload=payload,
        )
        audio_url = find_nested_string(response, ("audio_url", "url"))
        if not audio_url:
            raise ProviderResponseError(
                "speech response is missing an output URL",
                provider=self.provider_name,
                operation="synthesize speech",
            )
        response_id = request_id(response)
        self.budget.charge(
            cost,
            agent="sound_designer",
            model=self.model,
            note=note,
            details={
                "request_id": response_id,
                "characters": len(text),
                "voice": voice,
                "format": audio_format,
            },
        )
        raw = download_bytes(
            self.session,
            audio_url,
            provider=self.provider_name,
            operation="download speech",
            api_key=key,
            timeout=self.download_timeout,
            max_bytes=self.max_download_bytes,
        )
        if not raw:
            raise ProviderResponseError(
                "downloaded speech is empty",
                provider=self.provider_name,
                operation="download speech",
            )
        path = atomic_write(output_path, raw)
        return AudioResult(
            path=path,
            model=self.model,
            cost_cny=cost,
            request_id=response_id,
        )
