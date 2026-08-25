# 电影 Agent 评分标准对照

本表把可由仓库机器验证的工程证据，与必须由评委观看或创作者账号确认的证据分开。运行 `python scripts/check_submission.py` 可刷新当前缺口；该命令不联网、不产生费用。

| 维度 | 对应实现与证据 | 当前边界 |
|---|---|---|
| 多 Agent Harness（30） | 50 步类型化 DAG；八个角色 Agent；依赖、状态、上下文、预算、脱敏账本；VLM 审片有限重试；步骤显式标注 local/cloud/hybrid；锚点与 Go/No-Go 人工门禁 | 真实全片运行需批准锚点、有效新凭据和付费确认 |
| 一句话生成测试（25） | `lumen create "一句话"` 默认零网络输出任务计划与最坏报价；`--execute --confirm-spend` 执行 I2V 单镜和三帧审片，并保存视频与 JSON 证据 | 标准入口是单镜测试，不冒充完整 100 秒成片 |
| 技术创新与模型工程（25） | Provider 能力适配、主/稳/低成本降级、可执行批评回灌、最多两次自动修正、预算熔断、缓存恢复、请求级 BYOK、便携 ffmpeg | 未使用微调或量化，不在申报材料中虚构这些能力 |
| 自主作品质量（10） | 14 镜、95 秒镜头 + 5 秒片尾的完整叙事契约；四组原创视觉锚点；本地生成的严格 15 秒概念预告 | `final.mp4` 出现并通过人工观看前，该项不能宣称完成 |
| 复现、开源与部署（10） | MIT、README、锁定依赖、测试、Quickstart Notebook、CI、提交审计、根目录 ModelScope `app.py`/`requirements.txt` | 创空间 URL、文章 URL、最终视频 URL 仍需账号持有人填写 |

## 评审现场最短路径

```bash
uv sync --all-extras
uv run lumen validate projects/vanishing-light/film.yaml
uv run lumen run projects/vanishing-light/film.yaml --dry-run
uv run lumen create "最后一座灯塔熄灭前，守塔人看见海面升起第二个太阳。"
uv run pytest
uv run python scripts/check_submission.py
uv run python studio/app.py
```

完整 live Harness 使用：

```bash
uv run lumen run projects/vanishing-light/film.yaml --mode live --confirm-spend
```

它会复用既有通过产物，并在尚未批准的视觉锚点或缺失 Go/No-Go 决策处明确暂停。只有显式确认付费后才会创建付费 Provider 请求。
