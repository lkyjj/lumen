# Provider notes verified on 2026-08-26

These are integration notes, not permanent guarantees. Re-check model availability, region, quota
and price in the console immediately before a paid run.

## ModelScope

- OpenAI-compatible base URL: `https://api-inference.modelscope.cn/v1`.
- Planned text model: `Qwen/Qwen3.5-35B-A3B`.
- Planned visual critic: `Qwen/Qwen3-VL-8B-Instruct`.
- Free service limits include a 2,000-call daily account total and a maximum of 200 calls per model;
  dynamic throttling applies and there is no production SLA.

References: [API-Inference](https://modelscope.cn/docs/model-service/API-Inference/intro),
[limits](https://modelscope.cn/docs/model-service/API-Inference/limits).

## DashScope native API

- Prefer the Beijing business-workspace domain when the account supplies a workspace ID.
- Video task creation:
  `POST /services/aigc/video-generation/video-synthesis` with
  `X-DashScope-Async: enable`.
- Task polling: `GET /tasks/{task_id}` roughly every 15 seconds.
- Task/result URLs expire; successful output is downloaded immediately.
- Wan 2.6 T2I: `POST /services/aigc/multimodal-generation/generation`.
- CosyVoice non-realtime: `POST /services/audio/tts/SpeechSynthesizer`.
- Default TTS is `cosyvoice-v3-flash` because it supports system voices. The v3.5 plus/flash
  family requires a cloned or designed voice and cannot use system voices.

References:

- [Base URL and regions](https://help.aliyun.com/zh/model-studio/base-url)
- [Wan 3.0](https://help.aliyun.com/zh/model-studio/wan3-video-generation-api-reference)
- [Wan 2.7 I2V](https://help.aliyun.com/zh/model-studio/image-to-video-general-api-reference)
- [Wan 2.1–2.6 I2V](https://help.aliyun.com/zh/model-studio/legacy-image-to-video-api-reference/)
- [Wan 2.6 T2I](https://help.aliyun.com/zh/model-studio/text-to-image-v2-api-reference)
- [Async tasks](https://help.aliyun.com/en/model-studio/manage-asynchronous-tasks)
- [CosyVoice HTTP](https://help.aliyun.com/zh/model-studio/cosyvoice-tts-http-api)
- [Pricing](https://help.aliyun.com/zh/model-studio/model-pricing)

## Failure policy

- 400: fail fast and show a redacted contract error.
- 401/403: fail fast; do not retry permission, region or invitation failures.
- 429: exponential backoff with jitter within the configured retry/timeout budget.
- 5xx/network timeout: bounded retry for idempotent status requests; creation retries require a task
  lookup or idempotency evidence to avoid duplicate billing.
