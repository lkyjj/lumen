from __future__ import annotations

import base64
import wave
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from lumen.providers import (
    DashScopeT2IProvider,
    DashScopeTTSProvider,
    DashScopeVideoProvider,
    FakeImageProvider,
    FakeLLMProvider,
    FakeTTSProvider,
    FakeVideoProvider,
    FakeVLMProvider,
    ModelScopeProvider,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderTransportError,
    UnsupportedModelError,
)
from lumen.providers.media import image_to_data_url


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: object | None = None,
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.content = content

    def json(self) -> object:
        return self.payload

    def iter_content(self, chunk_size: int) -> list[bytes]:
        return [
            self.content[index : index + chunk_size]
            for index in range(0, len(self.content), chunk_size)
        ]


class QueueSession:
    def __init__(self, responses: list[FakeResponse | Exception], events: list[str]) -> None:
        self.responses = list(responses)
        self.events = events
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.events.append(f"request:{method}")
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self.responses:
            raise AssertionError(f"unexpected network call: {method} {url}")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class RecordingBudget:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.checks: list[tuple[float, str]] = []
        self.charges: list[dict[str, Any]] = []

    def check(self, amount: float, *, note: str = "") -> None:
        self.events.append("budget:check")
        self.checks.append((amount, note))

    def charge(
        self,
        amount: float,
        *,
        agent: str,
        model: str,
        note: str = "",
        details: dict[str, Any] | None = None,
        reserved: bool = False,
    ) -> None:
        self.events.append("budget:charge")
        self.charges.append(
            {
                "amount": amount,
                "agent": agent,
                "model": model,
                "note": note,
                "details": details,
                "reserved": reserved,
            }
        )


class OpenAIClientFactory:
    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = list(responses)
        self.keys: list[str] = []
        self.base_urls: list[str] = []
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *, api_key: str, base_url: str) -> object:
        self.keys.append(api_key)
        self.base_urls.append(base_url)
        completions = SimpleNamespace(create=self._create)
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    def _create(self, **kwargs: Any) -> object:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        message = SimpleNamespace(content=response)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def png_bytes(
    size: tuple[int, int] = (320, 240),
    *,
    mode: str = "RGB",
) -> bytes:
    image = Image.new(mode, size, color=(40, 80, 120, 128) if mode == "RGBA" else (40, 80, 120))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def write_reference(path: Path, *, mode: str = "RGB") -> None:
    path.write_bytes(png_bytes(mode=mode))


def test_modelscope_request_key_and_strict_json_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODELSCOPE_API_KEY", "environment-secret")
    factory = OpenAIClientFactory(["not json", '{"approved": true}'])
    provider = ModelScopeProvider(client_factory=factory)

    result = provider.chat_json(
        model="Qwen/Qwen3.5-35B-A3B",
        system="Return a decision.",
        user="Review scene one.",
        api_key="request-secret",
    )

    assert result == {"approved": True}
    assert factory.keys == ["request-secret", "request-secret"]
    assert factory.base_urls == [
        "https://api-inference.modelscope.cn/v1",
        "https://api-inference.modelscope.cn/v1",
    ]
    retry_messages = factory.calls[1]["messages"]
    assert retry_messages[-2] == {"role": "assistant", "content": "not json"}
    assert "只返回 JSON" in retry_messages[-1]["content"]


def test_modelscope_vision_content_and_environment_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODELSCOPE_API_KEY", "environment-secret")
    factory = OpenAIClientFactory(['{"score": 8}'])
    provider = ModelScopeProvider(client_factory=factory)

    result = provider.vision_json(
        model="Qwen/Qwen3-VL-8B-Instruct",
        system="Act as a critic.",
        text="Check continuity.",
        image_data_urls=["data:image/png;base64,AAAA", "data:image/png;base64,BBBB"],
    )

    assert result == {"score": 8}
    assert factory.keys == ["environment-secret"]
    content = factory.calls[0]["messages"][1]["content"]
    assert content[0] == {"type": "text", "text": "Check continuity."}
    assert content[1]["image_url"]["url"].endswith("AAAA")
    assert content[2]["image_url"]["url"].endswith("BBBB")


def test_modelscope_errors_redact_secrets_and_data_urls() -> None:
    secret = "provider-secret-value"
    leaked = f"Authorization: Bearer {secret} data:image/png;base64,AAAA"
    factory = OpenAIClientFactory([RuntimeError(leaked)])
    provider = ModelScopeProvider(api_key=secret, client_factory=factory)

    with pytest.raises(ProviderTransportError) as caught:
        provider.chat(model="model", messages=[{"role": "user", "content": "hello"}])

    message = str(caught.value)
    assert secret not in message
    assert "AAAA" not in message
    assert "[REDACTED]" in message


def test_image_data_url_flattens_to_rgb_and_enforces_dimensions(tmp_path: Path) -> None:
    reference = tmp_path / "reference.png"
    write_reference(reference, mode="RGBA")

    encoded = image_to_data_url(reference)

    assert (encoded.width, encoded.height) == (320, 240)
    assert encoded.encoded_bytes <= 20 * 1024 * 1024
    assert encoded.value.startswith("data:image/png;base64,")
    raw = base64.b64decode(encoded.value.partition(",")[2])
    with Image.open(BytesIO(raw)) as decoded:
        assert decoded.mode == "RGB"
        assert decoded.size == (320, 240)

    too_small = tmp_path / "small.png"
    too_small.write_bytes(png_bytes((239, 240)))
    with pytest.raises(ValueError, match="width"):
        image_to_data_url(too_small)


def test_dashscope_t2i_checks_budget_charges_and_downloads_rgb(tmp_path: Path) -> None:
    events: list[str] = []
    budget = RecordingBudget(events)
    session = QueueSession(
        [
            FakeResponse(
                payload={
                    "output": {
                        "choices": [{"message": {"content": [{"image": "https://result/image"}]}}]
                    },
                    "request_id": "image-request",
                }
            ),
            FakeResponse(content=png_bytes(mode="RGBA")),
        ],
        events,
    )
    output = tmp_path / "anchor.jpg"
    provider = DashScopeT2IProvider(
        budget=budget,
        api_key="dashscope-secret",
        base_url="https://workspace.example/api/v1",
        session=session,
    )

    result = provider.generate("cinematic figure", output)

    assert events == ["budget:check", "request:POST", "budget:charge", "request:GET"]
    assert result.path == output
    assert result.cost_cny == 0.2
    assert budget.charges[0]["model"] == "wan2.6-t2i"
    payload = session.calls[0]["json"]
    assert payload["parameters"]["size"] == "1696*960"
    assert payload["input"]["messages"][0]["content"] == [{"text": "cinematic figure"}]
    with Image.open(output) as saved:
        assert saved.mode == "RGB"


@pytest.mark.parametrize(
    ("model", "input_field", "has_ratio", "has_audio"),
    [
        ("wan3.0-video", "media", True, True),
        ("wan2.7-i2v-2026-04-25", "media", False, False),
        ("wan2.6-i2v-flash", "img_url", False, True),
    ],
)
def test_dashscope_video_capability_payload_and_async_download(
    tmp_path: Path,
    model: str,
    input_field: str,
    has_ratio: bool,
    has_audio: bool,
) -> None:
    events: list[str] = []
    budget = RecordingBudget(events)
    session = QueueSession(
        [
            FakeResponse(payload={"output": {"task_id": "task-123"}, "request_id": "created"}),
            FakeResponse(payload={"output": {"task_status": "RUNNING"}}),
            FakeResponse(
                payload={
                    "output": {
                        "task_status": "SUCCEEDED",
                        "video_url": "https://result/video",
                    },
                    "usage": {"video_duration": 5},
                    "request_id": "completed",
                }
            ),
            FakeResponse(content=b"video-result"),
        ],
        events,
    )
    clock = FakeClock()
    reference = tmp_path / f"{model}.png"
    write_reference(reference)
    output = tmp_path / f"{model}.mp4"
    provider = DashScopeVideoProvider(
        model=model,
        budget=budget,
        api_key="dashscope-secret",
        base_url="https://workspace.example/api/v1",
        session=session,
        clock=clock,
        sleeper=clock.sleep,
    )

    result = provider.generate_from_image(
        "subtle head turn",
        reference,
        output,
        poll_interval=1,
        poll_timeout=10,
    )

    assert events == [
        "budget:check",
        "request:POST",
        "request:GET",
        "request:GET",
        "budget:charge",
        "request:GET",
    ]
    assert result.path.read_bytes() == b"video-result"
    assert result.request_id == "completed"
    assert result.usage == {"video_duration": 5}
    submit = session.calls[0]
    assert submit["headers"]["X-DashScope-Async"] == "enable"
    payload = submit["json"]
    assert input_field in payload["input"]
    if input_field == "media":
        assert payload["input"]["media"][0]["url"].startswith("data:image/png;base64,")
        assert "img_url" not in payload["input"]
    else:
        assert payload["input"]["img_url"].startswith("data:image/png;base64,")
        assert "media" not in payload["input"]
    assert ("ratio" in payload["parameters"]) is has_ratio
    assert ("audio" in payload["parameters"]) is has_audio
    if has_audio:
        assert payload["parameters"]["audio"] is False


def test_dashscope_video_failure_is_redacted_and_not_charged(tmp_path: Path) -> None:
    events: list[str] = []
    budget = RecordingBudget(events)
    secret = "dashscope-secret-value"
    session = QueueSession(
        [
            FakeResponse(payload={"output": {"task_id": "task-failed"}}),
            FakeResponse(
                payload={
                    "output": {
                        "task_status": "FAILED",
                        "code": "InvalidInput",
                        "message": f"{secret} data:image/png;base64,AAAA",
                    }
                }
            ),
        ],
        events,
    )
    reference = tmp_path / "reference.png"
    write_reference(reference)
    provider = DashScopeVideoProvider(
        model="wan2.6-i2v-flash",
        budget=budget,
        api_key=secret,
        session=session,
    )

    with pytest.raises(ProviderResponseError) as caught:
        provider.generate_from_image(
            "move",
            reference,
            tmp_path / "result.mp4",
            poll_interval=1,
        )

    assert secret not in str(caught.value)
    assert "AAAA" not in str(caught.value)
    assert not budget.charges


def test_dashscope_video_poll_has_finite_timeout(tmp_path: Path) -> None:
    events: list[str] = []
    budget = RecordingBudget(events)
    session = QueueSession(
        [
            FakeResponse(payload={"output": {"task_id": "task-running"}}),
            FakeResponse(payload={"output": {"task_status": "PENDING"}}),
            FakeResponse(payload={"output": {"task_status": "RUNNING"}}),
            FakeResponse(payload={"output": {"task_status": "RUNNING"}}),
        ],
        events,
    )
    clock = FakeClock()
    reference = tmp_path / "reference.png"
    write_reference(reference)
    provider = DashScopeVideoProvider(
        model="wan2.7-i2v-2026-04-25",
        budget=budget,
        api_key="dashscope-secret",
        session=session,
        clock=clock,
        sleeper=clock.sleep,
    )

    with pytest.raises(ProviderTimeoutError):
        provider.generate_from_image(
            "move",
            reference,
            tmp_path / "result.mp4",
            poll_interval=0.6,
            poll_timeout=1,
        )

    assert not budget.charges


def test_unsupported_video_model_fails_before_any_request() -> None:
    with pytest.raises(UnsupportedModelError):
        DashScopeVideoProvider(
            model="wan-unknown",
            budget=RecordingBudget([]),
            api_key="unused",
            session=QueueSession([], []),
        )


def test_dashscope_tts_non_realtime_budget_and_immediate_download(tmp_path: Path) -> None:
    events: list[str] = []
    budget = RecordingBudget(events)
    session = QueueSession(
        [
            FakeResponse(
                payload={
                    "output": {"audio": {"url": "https://result/audio"}},
                    "request_id": "speech-request",
                }
            ),
            FakeResponse(content=b"RIFF-fake-wave"),
        ],
        events,
    )
    output = tmp_path / "voice.wav"
    provider = DashScopeTTSProvider(
        budget=budget,
        api_key="dashscope-secret",
        base_url="https://workspace.example/api/v1",
        session=session,
        price_cny_per_10k_chars=2_000,
    )

    result = provider.synthesize(
        "你好世界",
        output,
        voice="longxiaochun_v3",
        instruction="平静而克制",
    )

    assert events == ["budget:check", "request:POST", "budget:charge", "request:GET"]
    assert result.path.read_bytes() == b"RIFF-fake-wave"
    assert result.cost_cny == 0.8
    payload = session.calls[0]["json"]
    assert payload["input"]["voice"] == "longxiaochun_v3"
    assert payload["input"]["instruction"] == "平静而克制"
    assert payload["input"]["sample_rate"] == 24_000
    assert payload["input"]["format"] == "wav"
    assert "parameters" not in payload


def test_all_fake_providers_are_deterministic_and_offline(tmp_path: Path) -> None:
    llm = FakeLLMProvider([{"scene": 1}])
    assert llm.chat_json(model="fake", system="system", user="user") == {"scene": 1}

    vlm = FakeVLMProvider([{"continuity": "ok"}])
    assert vlm.vision_json(
        model="fake-vlm",
        system="critic",
        text="compare",
        image_data_urls=["data:image/png;base64,AAAA"],
    ) == {"continuity": "ok"}

    image = FakeImageProvider().generate("anchor", tmp_path / "fake.png")
    with Image.open(image.path) as rendered:
        assert rendered.mode == "RGB"
        assert rendered.size == (320, 240)

    video = FakeVideoProvider(content=b"offline-video").generate_from_image(
        "move",
        image.path,
        tmp_path / "fake.mp4",
    )
    assert video.path.read_bytes() == b"offline-video"

    audio = FakeTTSProvider().synthesize("hello", tmp_path / "fake.wav", voice="fake")
    with wave.open(str(audio.path), "rb") as generated:
        assert generated.getframerate() == 24_000
        assert generated.getnchannels() == 1


def test_http_provider_error_uses_only_safe_response_fields(tmp_path: Path) -> None:
    events: list[str] = []
    secret = "dashscope-secret-value"
    session = QueueSession(
        [
            FakeResponse(
                status_code=401,
                payload={
                    "code": "InvalidApiKey",
                    "message": f"bad Authorization: Bearer {secret}",
                    "request": {"headers": {"Authorization": secret}},
                },
            )
        ],
        events,
    )
    provider = DashScopeT2IProvider(
        budget=RecordingBudget(events),
        api_key=secret,
        session=session,
    )

    with pytest.raises(ProviderTransportError) as caught:
        provider.generate("anchor", tmp_path / "unused.png")

    assert secret not in str(caught.value)
    assert "request" not in str(caught.value)
    assert events == ["budget:check", "request:POST"]
