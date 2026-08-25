# LUMEN 开工交接清单
### 你要准备什么 · 什么不用准备 · 怎么把项目交给 AI

> 配套文档：《消失的光芒×LUMEN-参赛计划.md》
> 用法：**把计划书和本文件都放进仓库根目录**，然后照 §5 把开工消息粘给 Qoder。

---

## 0. 先划掉一件你以为要做的事

**不需要 OSS，不需要图床，不需要任何对象存储凭证。**

百炼的 `media[].url` 支持三种形式，其中 Base64 是零依赖的：

| 形式 | 写法 |
|---|---|
| 公网 URL | `https://xxx/xxx.png` |
| **Base64 Data URL ← 本方案用这个** | `data:image/png;base64,iVBOR...` |
| 百炼临时 URL | `oss://dashscope-instant/xxx.png`（百炼自带上传接口，非你的 OSS） |

Python SDK 另外还支持 `file://` 本地路径。所以锚点图直接从本地读、编码、塞进请求就行。

> ⚠️ 唯一要注意的：**PNG 不支持透明通道**。AI 生成的图经常带 alpha，存盘前用 Pillow `convert("RGB")` 压平。
> 其他限制：JPEG/JPG/PNG/BMP/WEBP，单边 240–8000 px，长宽比 ≤ 8:1，≤ 20MB。

---

## 1. 只有你能提供的

### A. 凭证 —— **必需只有 2 个**

| 环境变量 | 去哪拿 | 必需 | 关键注意 |
|---|---|---|---|
| `MODELSCOPE_API_KEY` | modelscope.cn → 账号设置 → 访问令牌 → 新建 SDK Token | ✅ | **必须勾选「大模型推理」权限**，否则调用报 403。格式 `ms-xxxxxxxx` |
| `DASHSCOPE_API_KEY` | bailian.console.aliyun.com → API-KEY | ✅ | **地域必须选华北2·北京**，新人免费额度只在北京生效。格式 `sk-xxxxxxxx` |
| `MODELSCOPE_GIT_TOKEN` | 同第一个，通常是同一个 token | 推创空间时 | 用在 `https://oauth2:<token>@www.modelscope.cn/studios/...` |
| `DASHSCOPE_WORKSPACE_ID` | 百炼控制台工作空间详情 | ❌ 可选 | 只有改用新域名 `{WorkspaceId}.cn-beijing.maas.aliyuncs.com` 才需要。旧域名仍可用 |
| ~~`OSS_ACCESS_KEY_*`~~ | — | ❌ **不需要** | 见 §0 |

### B. 地址与名字 —— 4 个

| 项 | 例子 | 用途 |
|---|---|---|
| GitHub 仓库地址 | `git@github.com:你的用户名/lumen.git` | 代码托管，**必须公开**（评委要看 `.qoder/`） |
| 魔搭用户名 | `your_ms_name` | 拼创空间 git 地址用 |
| 创空间名字 | `lumen`（你自己定） | → `modelscope.cn/studios/your_ms_name/lumen` |
| 本地项目绝对路径 | `~/projects/lumen` | 告诉 Qoder 在哪工作 |

### C. 环境信息 —— 3 个

告诉 AI 这三条，它才知道给你什么命令：

- 操作系统与芯片：macOS(Apple Silicon / Intel) / Windows / Linux
- Python 版本：`python3 -V`（需 3.11+）
- ffmpeg 装没装：`ffmpeg -version`（**审片抽帧和剪辑都依赖它，必装**）

### D. 需要你亲自拍板的 —— 2 个

这两件事 AI 做不了决定，必须你看着定：

1. **E-06 的角色锚点图定稿**（D7）。AI 能生成一百张，但"就是这张"只能你说了算。这张图决定全片成败。
2. **D9 的 Go / No-Go**。试拍后角色一致性到底守没守住——守住了继续，没守住立刻切 Plan B（全程背影 + 手部 + 剪影）。**这个判断只能人来做。**

---

## 2. 这些**不用**你提供（计划书里已经有了）

别浪费时间重新组织这些内容，直接让 AI 读 `PLAN.md`：

| 内容 | 在计划书哪一节 |
|---|---|
| 完整剧本与 14 镜分镜表（含每镜时长/景别/运镜/声音） | §3.4 |
| `film.yaml` 完整结构与字段定义 | §4.5 |
| 8 个 Agent 的职责划分与数据流 | §4.2 – §4.3 |
| 目录结构 | §4.4 |
| 5 段关键代码骨架（契约/LLM/视频/审片/预算） | §4.6 |
| `.qoder/rules` 三个文件的完整内容 | §5.1 |
| `.qoder/agents` 自定义 Agent 的完整内容 | §5.2 |
| 所有模型 ID、API 端点、参数结构 | §6.2、§4.6 |
| 创空间部署方案与 `app.py` 骨架 | §7 |
| 19 天排期与每日验收标准 | §8 |

---

## 3. 有等待时间的 —— 今天就启动

按阻塞程度排序，前两条不做完后面全卡住：

1. **阿里云账号实名认证** —— 个人一般即时，企业可能 1–2 天。**这是所有事情的前置**
2. **魔搭绑定阿里云账号** —— 不绑定，免费推理额度不激活
3. **百炼开通 + 确认免费额度到账** —— 90 天有效期、仅北京地域、**不同模型额度独立不互通**
4. **Qoder 安装 + 确认剩余 Credits** —— 报名奖励的 500 Credits 要等报名审核后才到

> 第 4 条反推出一个结论：**今天先发小红书报名帖**（计划书 §12 有现成文案），Credits 才能早点到账，否则前几天开发只能吃自己的额度。

---

## 4. `.env.example`

放进仓库根目录，**同时把 `.env` 写进 `.gitignore`**：

```bash
# ── 必需 ────────────────────────────────────────
# 魔搭：LLM(编剧/分镜) + VLM(审片)。免费 2000 次/天
# 注意创建 token 时必须勾选「大模型推理」权限
MODELSCOPE_API_KEY=ms-xxxxxxxxxxxxxxxx

# 百炼：视频生成 + 文生图 + TTS。地域必须是华北2·北京
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# ── 可选 ────────────────────────────────────────
# 推送创空间用，通常与 MODELSCOPE_API_KEY 相同
MODELSCOPE_GIT_TOKEN=ms-xxxxxxxxxxxxxxxx

# 仅当改用新域名 {WorkspaceId}.cn-beijing.maas.aliyuncs.com 时需要
# DASHSCOPE_WORKSPACE_ID=llm-xxxxxxxx

# ── 项目配置 ────────────────────────────────────
MODELSCOPE_USER=your_ms_username
STUDIO_NAME=lumen

# 预算硬上限（元）。到顶熔断，不是警告
LUMEN_BUDGET_CAP=300
LUMEN_BUDGET_WARN=200
```

---

## 5. 粘给 Qoder 的第一条消息

把 `PLAN.md` 和本文件放进仓库根目录后，**原样粘贴下面这段**：

```
我在参加「AI+∞ 开发者创作大赛」第二期，主赛道是「电影 Agent」。
完整方案见仓库根目录的 PLAN.md，请先完整读一遍再动手——里面有剧本、
分镜表、架构设计、代码骨架、模型 ID 和 API 参数结构，不要重新设计。

项目叫 LUMEN：一个 8 Agent 的电影生产系统，产出物是一部 95 秒的
科幻短片《消失的光芒》。

【我的环境】
- 操作系统：<填 macOS(M系列) / Windows / Linux>
- Python：<填版本>
- ffmpeg：<已装 / 未装>
- 项目路径：<填绝对路径>

【凭证】
已放在 .env（不提交 Git）：
- MODELSCOPE_API_KEY  魔搭，OpenAI 兼容，base_url=https://api-inference.modelscope.cn/v1
- DASHSCOPE_API_KEY   百炼，视频/图像/TTS

【今天要做的（对应 PLAN.md 的 D2–D3）】
1. 按 PLAN.md §4.4 建目录结构
2. 按 §4.6 ① 写 lumen/contracts.py，先把数据契约定死
3. 按 §5.1 把三个 rules 文件写到 .qoder/rules/
4. 建 lumen/cli.py，实现 `lumen run --dry-run film.yaml`：
   只打印完整 DAG 和每步预估花费，不真的调任何 API

【三条铁律，任何时候不能违反】
1. 任何花钱的调用（视频/图像生成）必须先过 Budget.check()，
   成功后 Budget.charge() 记账。没有例外。
2. wan3.0-video 的参考图用 input.media 数组，不是 img_url。
   img_url 是 wan2.x 的写法。见 PLAN.md §4.6 的警示框。
3. API Key 只从环境变量读，绝不写进代码、配置或日志。

先只做上面 4 步，做完停下来给我看，不要一口气把整个项目写完。
```

> **最后那句很重要。** 让它一次只做一个阶段，你才有机会在方向跑偏之前拉回来——也才省 Credits。

---

## 6. D1 验证脚本

两个 Key 拿到后立刻跑这个，**不要等到 D4 才发现权限没勾**：

```bash
#!/usr/bin/env bash
set -e
source .env

echo "── 1. 魔搭 LLM ──"
curl -s https://api-inference.modelscope.cn/v1/chat/completions \
  -H "Authorization: Bearer $MODELSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B","messages":[{"role":"user","content":"回复OK两个字"}]}' \
  | head -c 300; echo

echo "── 2. 魔搭 VLM（审片要用）──"
curl -s https://api-inference.modelscope.cn/v1/models \
  -H "Authorization: Bearer $MODELSCOPE_API_KEY" \
  | grep -o 'Qwen/Qwen3-VL-8B-Instruct' | head -1

echo "── 3. 百炼视频（会消耗少量免费额度，值得）──"
curl -s -X POST \
  'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis' \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H 'X-DashScope-Async: enable' \
  -H 'Content-Type: application/json' \
  -d '{"model":"wan2.6-i2v-flash","input":{"prompt":"海面，无光，静止"}}' \
  | head -c 300; echo

echo "── 4. ffmpeg ──"
ffmpeg -version | head -1
```

**四条全过，才算 D1 完成。**

- 第 1 条失败 → token 没勾「大模型推理」权限
- 第 3 条报额度错误 → 百炼没开通，或地域不是华北2·北京
- 第 3 条报参数错误 → 正常，说明鉴权通了

---

## 7. 一句话总结

**你要给 AI 的，只有 2 个 Key、4 个地址、3 条环境信息。**
剧本、架构、代码、模型 ID、参数结构全在 `PLAN.md` 里，让它自己读。

**AI 替不了你的，只有 2 件事**：锚点图定稿，和 D9 那个 Go/No-Go 判断。
