# 《消失的光芒》× LUMEN
### AI+∞ 开发者创作大赛 · 第二期「用 AI，提前看见未来」· 完整参赛计划

> 赛道定位：**以「进阶创作｜电影 Agent」为主赛道**，短片《消失的光芒》作为该 Agent 的首个产出物同时投「原创 AI 科幻短片」。
> 算力路线：**纯云端**（魔搭 API-Inference + 阿里云百炼 + 魔搭创空间），零硬件门槛。
> 编制日期：2026-08-26 ｜ 距提交截止 **19 天**

---

## 0. 一页速览

| 项 | 内容 |
|---|---|
| **作品名** | 《消失的光芒》The Vanishing Light |
| **系统名** | **LUMEN** —— 一个人的 AI 电影剧组 |
| **一句话** | 我没有拍一部片子，我造了一个会拍片子的剧组，然后让它拍了第一部片子。 |
| **短片形态** | 95 秒 · 单人 · 单空间 · 零对口型 · 14 个镜头 |
| **Agent 形态** | 8 个角色 Agent + 1 份 `film.yaml` 契约 + 审片重拍闭环，`lumen run` 一键复现 |
| **核心差异化** | ① 视觉一致性锚点系统 ② VLM 审片自动重拍闭环 ③ 预算硬熔断 ④ 整部电影可版本控制、可复现 |
| **预计现金成本** | **¥110 – ¥150**（hard cap 设 ¥300） |
| **两条死线** | 报名 **9/14 12:00** ｜ 提交 **9/14 22:00**（北京时间，报名比提交早 10 小时） |
| **最紧急动作** | **今天就把小红书报名帖发出去**，拿 500 Qoder Credits 用于后续开发 |

---

## 1. 比赛事实核对

开工前先把规则钉死，避免最后两天返工。

### 1.1 官方信息

| 项 | 内容 |
|---|---|
| 比赛官网（报名 + 提交都在这） | https://mseo-ai-inf.ms.show/ |
| 魔搭侧入口 | https://modelscope.cn/active/AIstudio |
| 主办方 | 魔搭社区 ModelScope × Qoder |
| 本期主题 | AI + 影视流 /「用 AI，提前看见未来」 |
| 创作手记发布地 | 魔搭开发者实践 https://modelscope.cn/learn （页面「创建内容」按钮） |

### 1.2 时间轴（北京时间）

```
08-19  ├─ 赛事开始
       │
08-26  ├─ ★ 今天。D1
       │
09-14  ├─ 12:00  ★★ 报名截止（发帖 + 官网提交链接）
       ├─ 22:00  ★★ 作品提交截止
09-15  ├─ 评审开始
09-18  ├─ 评审结束
09-19  └─ 公布结果
```

> ⚠️ **最容易踩的坑**：报名截止（12:00）比提交截止（22:00）早 10 小时。很多人以为都是 22:00，结果中午就失去资格。
> **对策：报名今天做完，不要拖。**

### 1.3 两条赛道的提交物

**赛道一 · 原创 AI 科幻短片**（1–5 分钟）

1. 视频外链 —— B 站（官方推荐）/ 小红书 / 抖音 任一
2. 原视频文件 —— 官网直接上传
3. 创作手记 —— 发在魔搭开发者实践，提交链接

**赛道二 · 进阶创作｜电影 Agent**

1. 电影 Agent 部署到**魔搭创空间**的作品链接
2. 创作手记（记录创作过程、工作流设计、所用模型与工具）

> 从第一期获奖名单看，**每一位获奖者都同时有「作品链接」和「开发者实践手记」两条链接**——创作手记不是可选项，是评奖必要材料。

### 1.4 奖项（第一期实际数据，第二期未公布，作为参照）

| 奖项 | 奖金（含税） | 数量 |
|---|---|---|
| 一等奖 | ¥8,000 | 1 |
| 二等奖 | ¥5,000 | 1 |
| 三等奖 | ¥2,000 | 1 |
| 优秀创作奖 | ¥1,000 | 4 |
| 社交人气奖 | 未公布 | 2 |

参赛过程奖励：报名 500 Qoder Credits + 魔粒值 1000 ｜ 提交 1000 Qoder Credits + 魔粒值 2000

> 第一期公开投稿 **188 件**。这是一个"认真做就有机会"的量级——不是万人海选，但也不是随便交个东西就能进前七。

### 1.5 硬性限制（原文）

> 「你的作品里不要出现这些影片的角色、台词、造型、剧照与片名字样，同时不能侵犯肖像权。灵感可以来自它们，画面必须完全属于你。」

**对我们的约束**：角色形象必须是 AI 原生生成的虚构人物，不能用真人照片做参考图，不能出现任何已有科幻 IP 的视觉符号（不要机械姬的脸、不要银翼杀手的霓虹街、不要《流浪地球》的行星发动机）。本方案的美术方向是**低照度海边灯塔 + 冷蓝灰单光源**，天然远离这些符号。

---

## 2. 作品定位：一个作品，两条赛道

这是本方案最重要的一个结构性决策。

不要把「短片」和「电影 Agent」当成两个项目做。要把它们做成**同一件事的两个面**：

```
        ┌─────────────────────────────────────┐
        │      LUMEN · 一个人的 AI 电影剧组      │
        │        （赛道二：电影 Agent）          │
        └────────────────┬────────────────────┘
                         │  它的第一部作品
                         ▼
        ┌─────────────────────────────────────┐
        │   《消失的光芒》95 秒末日科幻短片       │
        │      （赛道一：原创 AI 科幻短片）       │
        └─────────────────────────────────────┘
```

**为什么这样最优：**

1. **工作量不是 1+1，是 1.3。** 短片是 Agent 跑出来的，做 Agent 的过程自然产出短片。反过来如果先手工剪片再补一个 Agent，等于做两遍。
2. **叙事上闭环，评委会记住。** 片中的「进化系统」是一个会自我升级的 AI；片外的 LUMEN 是一个会自我迭代的 AI 剧组。**片子讲的事情，正是造这部片子的方法。** 这个 meta 结构在创作手记里是杀手锏。
3. **直接命中官方文案。** 官方对赛道二的定义是「把制作一部电影的方法，变成一套持续创作的系统」——LUMEN 的 `film.yaml` 就是这句话的字面实现。

**创作手记的主标题就定为：**

> 《我造了一个会拍电影的剧组，然后让它拍了一部关于"进化的代价"的电影》

---

## 3. 短片方案：《消失的光芒》

### 3.1 先说为什么是这个形态

官方创作指南里有一段话，几乎是把答案写在题面上了：

> 「优先挑'一个人 + 一个空间 + 一件小事'的设定。本地视频模型最擅长氛围、特写、空镜与声音叙事，最不擅长复杂打斗与多人对口型——**90 秒一个好设定，胜过 5 分钟的宏大流水账**。」

你原本的「末日科技进化系统」题材，如果按网文思路展开（主角不断升级打怪、多方势力、宏大末世），**恰好落在模型最不擅长的每一项上**：多人、打斗、对白、场景切换。所以我做的第一件事是把它**收进一间屋子**——内核完全保留，形态彻底重构：

| 原始设定元素 | 保留方式 |
|---|---|
| 末日 | 不拍废墟和灾难，拍"没有太阳的海"——一个空镜就交代完 |
| 科技进化系统 | 不拍升级打怪，拍**一次进化机会**和它的代价 |
| 消失的光芒 | 双关做实：物理的光（世界最后一盏灯）+ 人身上的光（人性） |
| 系统流的爽感 | 反转成"拒绝系统"——这是更高级、也更适合 90 秒的处理 |

### 3.2 世界观（全部靠画面和声音交代，零解说旁白）

「大寂静」之后，天空覆盖着一层永不散去的尘幕，地表再也没有阳光。

活下来的人靠**进化系统**续命：一种植入式技术，消耗储备能源换取身体改造——更耐寒、更省氧、更不需要睡眠。代价是每一次进化都会带走一部分**"人的东西"**：感受温度的能力、流泪的能力、记住一张脸的能力。

系统很温和，从不强迫。它只是在你快撑不住的时候，礼貌地问一句：要不要再进化一次？

### 3.3 人物与空间

**人物（唯一出场角色）**

- 代号 **E-06**（意为：已完成 6 次进化）
- 亚洲男性，40 岁上下，短发凌乱，左脸有一道旧疤
- 左小臂以下是磨损的金属义肢，缝隙里透出微光
- **左眼是一枚发淡青光的光学元件，右眼还是人的眼睛**（这是全片最重要的视觉符号：他还剩一只人的眼睛）
- 深灰色旧防寒服，领口磨破

**空间（唯一场景）**

- 一座废弃海边灯塔的顶层控制室
- 落地弧形窗，窗外是黑色的海
- 室内唯一光源是一块老式仪表盘的微光
- 墙上有一把老式闸刀开关（灯塔总电源）

**一件小事**

- 电池只剩最后一格。
- 系统提示：这格电可以完成**第 7 次进化**（活下去），也可以**点亮灯塔 90 秒**（毫无用处——海上大概率已经没有人了）。

### 3.4 完整分镜表（14 镜 · 95 秒）

> 说明：`同机位` 标记的镜头共用同一张锚点参考图，这是保证一致性的关键设计，同时也是叙事设计——第 8 镜和第 3 镜是同一个座位、同一个角度，只是坐着的人不一样了。

| # | 时长 | 景别 / 运镜 | 画面内容 | 声音 |
|---|---|---|---|---|
| **01** | 7s | 大远景 · 极慢横移 | 灰蓝色的海。天空是一层厚重尘幕，没有太阳，没有月亮。海面上没有任何一点光。 | 风声、低频嗡鸣。无音乐 |
| **02** | 6s | 远景 · 固定 | 礁石上一座锈蚀的灯塔，灯室是黑的。浪拍在礁石根部。 | 加入海浪 |
| **03** | 5s | 中景 · 背影 · 固定 `锚点A` | 灯塔控制室内，一个人背对镜头坐着，面朝窗外的海。屋里唯一的光来自仪表盘。 | 电流声，微弱心跳 |
| **04** | 5s | 特写 · 固定 | 仪表盘：一格电量指示灯，缓慢闪烁。旁边的刻度全部归零。 | 滴答声 |
| **05** | 6s | 大特写 · 固定 | 他的双手放在膝上。右手是人的手，左手小臂以下是磨损金属义肢，缝隙里有一线微光。 | 义肢伺服的轻响 |
| **06** | 7s | 中近景 · 正面 · 极慢推 `锚点B` | 他的脸。右眼是人的眼睛，左眼是发淡光的光学元件。没有表情。 | 系统提示音首次出现 |
| **07** | 8s | 主观视角 POV | 他的视野里浮起半透明系统界面：`EVOLUTION 07 · READY` / `POWER REMAINING: 1` / `是否预演结果？` | 系统女声（冷）："进化程序 07 已就绪。剩余能源：1。是否预演结果？" |
| **08** | 8s | 中景 · **与 03 完全同机位** `锚点A` | **预演画面**：同一间屋、同一个座位，坐着"进化后的他"——躯体大部分已金属化，**两只眼睛都是光学元件**。他没有看窗外，正对着墙。色调更冷更蓝。 | 音乐首次进入：单音、极简、无旋律 |
| **09** | 6s | 大特写 · 固定 | 预演里那双眼睛：很亮，但没有反光，没有湿度。 | 音乐持续 |
| **10** | 7s | 闪回 · 降质画面 | **记忆残片**：多年前，同一扇窗，灯是亮的，光柱扫过海面。海面上有一艘小船正在往回开。画面有噪点、掉帧、色偏，像一段快要坏掉的录像。 | 音乐转暖，加入极轻的人声哼唱 |
| **11** | 6s | 特写 · 固定 `锚点B` | 回到现在。他的**右眼**里有一点水光。系统界面在闪：`EVOLUTION 07 · 00:09` | 心跳变强，倒计时电子音 |
| **12** | 7s | 中景 · 侧面 · 只见手 | 金属手抬起，悬在两个开关之间：一个刻着 `EVO`，一个是墙上的老式闸刀。……他握住了闸刀。 | **静音一拍**（关键留白）。他背对镜头轻声说：「……万一呢。」 |
| **13** | 9s | 大远景 · 缓慢升起 | 灯塔亮了。一道光柱扫过黑色海面，转了一圈，两圈。 | 音乐全开 |
| **14** | 8s | 大远景 · 固定 | 光熄灭。全黑。三秒后——遥远的海平线上，一个极小的光点亮起，闪了两下。 | 只剩风声，然后一声极轻的回应音 |

**结尾黑屏字幕（3s）**
```
SYSTEM LOG / 系统日志
E-06 拒绝进化。
原因：不可解析。
```

**片名字幕（2s）**
```
消 失 的 光 芒
THE VANISHING LIGHT
```

**总时长：95s + 5s 字幕 = 100 秒**

### 3.5 三个刻意的技术规避设计

这部分要写进创作手记——它证明你**懂模型的边界**，而不是在硬碰硬。

**① 零对口型。** 全片只有一句人声台词（第 12 镜），而且那一镜**只拍手，人物背对镜头**。所有其他人声都是"系统女声"——画外音，不需要任何嘴型匹配。这一条直接绕开了官方点名的最大短板。

**② 用"降质"把 AI 瑕疵变成美学。** 第 10 镜的记忆闪回，剧本设定就是"一段快要坏掉的录像"——噪点、掉帧、色偏、跳帧全是**剧情要求**。AI 生成视频最容易出现的那些不稳定，在这一镜里全部变成加分项。这是把劣势直接改判为优势。

**③ 同机位复用。** 03 / 08 / 11 三镜共用锚点，06 / 11 共用锚点。少一张独立参考图，就少一次一致性崩坏的机会；同时"同一个座位坐着不同的自己"本身就是叙事。

---

## 4. 电影 Agent 方案：LUMEN

### 4.1 定位

> **LUMEN 不是一个"用 AI 生成视频"的脚本，是一个把「拍电影」这件事拆成可调度、可审查、可重跑的工程系统。**
>
> 它的产出不只是一部片子，是一份 `film.yaml` —— 电影的**源代码**。改一行 logline 重跑，你得到另一部电影。

### 4.2 八个 Agent

| Agent | 中文 | 输入 | 输出 | 用什么模型 |
|---|---|---|---|---|
| `producer` | **制片** | `film.yaml` | 调度全流程 | 无（纯编排 + 预算逻辑） |
| `screenwriter` | **编剧** | logline | 结构化剧本 JSON | Qwen3.5-35B-A3B |
| `storyboarder` | **分镜** | 剧本 | 镜头表（景别/运镜/时长/情绪） | Qwen3.5-35B-A3B |
| `art_director` | **美术** | 人物设定 + 风格 | 锚点参考图（Character Bible） | Qwen-Image / wan2.6-t2i |
| `cinematographer` | **摄影** | 镜头表 + 锚点图 | 视频片段 | wan3.0-video（I2V 为主） |
| `sound_designer` | **声音** | 剧本 + 镜头表 | 人声 / 音效 / 配乐 | CosyVoice + ACE-Step |
| `editor` | **剪辑** | 片段 + 音轨 | 成片 | ffmpeg（无模型） |
| `critic` | **审片** | 生成的片段 + 分镜意图 | 评分 + 打回理由 | Qwen3-VL-8B-Instruct |

> 八个角色对应一个真实剧组的八个工种。这个映射本身就是给评委看的——**它不是"八个函数"，是"八个人"。**

### 4.3 数据流

```
  film.yaml
     │
     ▼
 ┌─────────┐
 │ 编剧     │──► script.json ─────────┐
 └─────────┘                          │
     │                                │
     ▼                                ▼
 ┌─────────┐                    ┌──────────┐
 │ 分镜     │──► shots.json ──►  │  声音     │──► *.wav
 └─────────┘         │          └──────────┘
     │               │
     ▼               │
 ┌─────────┐         │
 │ 美术     │──► bible/*.png
 └─────────┘         │
     │               │
     └───────┬───────┘
             ▼
       ┌──────────┐
       │  摄影     │──► clips/S01.mp4 …
       └────┬─────┘
            │              ┌──── 不合格：带理由重生成
            ▼              │      （最多 2 次）
       ┌──────────┐        │
       │  审片     │────────┘
       └────┬─────┘
            │ 合格
            ▼
       ┌──────────┐
       │  剪辑     │──► final.mp4
       └──────────┘
```

**这张图里最值钱的是「审片 → 重生成」那条回流线。** 没有它，这就是一条流水线脚本；有了它，才叫 Agent。

### 4.4 目录结构

```
lumen/
├── .qoder/                       # ★ Qoder 深度使用的证据，要提交到 Git
│   ├── rules/
│   │   ├── 00-project.md         # 项目铁律
│   │   ├── 10-film-language.md   # 影视语言规范（给写 prompt 的 Agent 看）
│   │   └── 20-api-contracts.md   # 各 Provider 的调用约定
│   ├── agents/                   # 自定义专家 Agent
│   │   ├── screenwriter.md
│   │   ├── storyboarder.md
│   │   ├── prompt-smith.md
│   │   └── critic.md
│   └── repowiki/                 # Repo Wiki 自动生成
│
├── lumen/
│   ├── cli.py                    # lumen run projects/vanishing-light/film.yaml
│   ├── orchestrator.py           # 制片 Agent：DAG 调度 / 重试 / 断点续跑
│   ├── contracts.py              # pydantic 数据契约（全系统的骨头）
│   ├── budget.py                 # 预算硬熔断
│   ├── agents/
│   │   ├── screenwriter.py
│   │   ├── storyboarder.py
│   │   ├── art_director.py
│   │   ├── cinematographer.py
│   │   ├── sound_designer.py
│   │   ├── editor.py
│   │   └── critic.py
│   └── providers/                # 模型接入层，全部可替换
│       ├── llm.py                # 魔搭 API-Inference（OpenAI 兼容）
│       ├── vlm.py                # 审片用视觉模型
│       ├── t2i.py                # 文生图
│       ├── video.py              # 百炼 wan3.0-video（异步任务）
│       ├── tts.py                # CosyVoice
│       └── music.py              # ACE-Step / 兜底素材
│
├── projects/
│   └── vanishing-light/
│       ├── film.yaml             # ★ 电影的源代码
│       ├── 01_script/
│       ├── 02_shots/
│       ├── 03_bible/             # 角色 / 场景锚点图
│       ├── 04_clips/
│       ├── 05_audio/
│       ├── 06_cut/
│       └── run.jsonl             # 全流程可追溯日志（含每次调用花了多少钱）
│
├── studio/                       # 魔搭创空间前端
│   ├── app.py                    # Gradio
│   └── requirements.txt
├── tests/
└── README.md
```

### 4.5 `film.yaml` —— 电影的源代码

这是整个方案的**契约核心**，也是创作手记里最该重点展示的东西。

```yaml
film:
  title: 消失的光芒
  title_en: The Vanishing Light
  logline: >
    末日之后，最后一个守灯人用仅剩的一格电，
    在"再进化一次活下去"和"点亮灯塔九十秒"之间做选择。
  duration_target: 100
  aspect_ratio: "16:9"
  resolution: 720P
  language: zh-CN

style:
  look: 低照度、冷蓝灰、单光源、颗粒感、类胶片
  palette: ["#0B1015", "#16232B", "#2E4A57", "#C8A46A"]
  camera: 固定机位为主，全片仅两次缓慢运动
  # ★ 负面清单：直接来自官方对模型短板的提示
  forbidden:
    - 多人同框
    - 对白口型特写
    - 快速动作与打斗
    - 手部精细操作
    - 任何已有科幻 IP 的视觉符号

cast:
  - id: E06
    name: 守灯人
    anchor_prompt: >
      亚洲男性，40岁上下，短发凌乱，左脸一道旧疤，
      左小臂以下为磨损金属义肢（缝隙透出微弱青光），
      左眼为发淡青光的光学元件、右眼为人类眼睛，
      深灰色旧防寒服，领口磨破。
    anchor_image: 03_bible/E06_front.png

locations:
  - id: LIGHTHOUSE_TOP
    anchor_prompt: >
      废弃海边灯塔顶层控制室，弧形落地窗，窗外是无光的黑色海面，
      室内唯一光源为老式仪表盘微光，墙上有老式闸刀开关。
    anchor_image: 03_bible/loc_lighthouse.png

budget:
  currency: CNY
  hard_cap: 300          # ★ 到顶即停，不是警告，是熔断
  warn_at: 200
  video_model: wan3.0-video
  fallback_video_model: wan2.6-i2v-flash   # 降级路线

quality_gate:
  min_score: 7.0
  max_retries: 2
  dimensions: [角色一致性, 构图符合分镜, 光线氛围, 无明显崩坏]

shots:
  - id: S03
    duration: 5
    size: 中景
    movement: 固定
    anchor: A                       # ★ 同机位复用
    cast: [E06]
    location: LIGHTHOUSE_TOP
    intent: 交代人物与空间的关系，人是背对我们的，我们和他一起看海
    prompt_seed: >
      灯塔控制室内，一个人背对镜头坐在椅子上，面朝弧形落地窗外的黑色海面，
      屋内唯一光源来自仪表盘微光，静止不动，电影感，低照度
    audio:
      sfx: [电流声, 微弱心跳]
      music: null

  - id: S08
    duration: 8
    size: 中景
    movement: 固定
    anchor: A                       # ★ 与 S03 同一张锚点图
    intent: 预演——同一个座位坐着进化后的自己，他不再看窗外
    prompt_seed: >
      同一间灯塔控制室，同一机位，椅子上坐着一个躯体大部分金属化的人形，
      双眼均为发光的光学元件，面朝墙壁而非窗外，色调更冷更蓝，静止
    audio:
      music: 单音极简
```

> **这个 YAML 就是对官方那句「把制作一部电影的方法，变成一套持续创作的系统」的直接回答。** 电影不再是一堆散落的素材和一个剪辑工程，而是一份可以 diff、可以 review、可以 rollback、可以 fork 的文本。

### 4.6 关键代码骨架

以下是四段"骨头"代码。它们不是完整实现，但定义了系统的形状——把这四段交给 Qoder，剩下的它能补。

#### ① 数据契约 `lumen/contracts.py`

先定契约，再写实现。这是让 8 个 Agent 能协作的前提。

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ShotAudio(BaseModel):
    voice: Optional[str] = None          # 台词文本，None 表示无人声
    voice_role: Literal["system", "human"] = "system"
    sfx: list[str] = []
    music: Optional[str] = None

class Shot(BaseModel):
    id: str
    duration: float
    size: str                            # 景别
    movement: str                        # 运镜
    anchor: Optional[str] = None         # 锚点复用标记
    cast: list[str] = []
    location: str
    intent: str                          # ★ 导演意图，审片 Agent 拿它当评分标准
    prompt_seed: str
    audio: ShotAudio = Field(default_factory=ShotAudio)

class ShotResult(BaseModel):
    shot_id: str
    clip_path: str
    attempt: int
    score: float
    critique: str                        # 审片理由，失败时回灌给摄影 Agent
    cost_cny: float
    passed: bool
```

#### ② LLM Provider `lumen/providers/llm.py`

魔搭 API-Inference 是 OpenAI 兼容的，所以直接用 `openai` SDK。每天 2000 次免费额度，写剧本和分镜完全够用。

```python
import os
from openai import OpenAI

_client = OpenAI(
    base_url="https://api-inference.modelscope.cn/v1",
    api_key=os.environ["MODELSCOPE_API_KEY"],   # ms-xxxxxxxx
)

DEFAULT_MODEL = "Qwen/Qwen3.5-35B-A3B"   # 免费额度内，性价比首选

def chat_json(system: str, user: str, model: str = DEFAULT_MODEL) -> dict:
    """要求模型返回严格 JSON，失败重试一次并把错误回灌。"""
    import json
    messages = [
        {"role": "system", "content": system + "\n\n只返回 JSON，不要任何解释文字、不要 markdown 代码块。"},
        {"role": "user", "content": user},
    ]
    for attempt in range(2):
        raw = _client.chat.completions.create(
            model=model, messages=messages, temperature=0.7,
        ).choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            if attempt == 1:
                raise
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"上面不是合法 JSON：{e}。请只输出修正后的 JSON。"},
            ]
```

#### ③ 视频 Provider `lumen/providers/video.py`

**这是全系统唯一花钱的地方**，所以它必须自带计价和熔断。百炼的视频接口是**异步两步式**：提交任务拿 `task_id`，再轮询。

```python
import os, time, requests

# 旧域名仍可用，但官方已建议迁移到工作空间域名：
#   https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api/v1
# 新域名需要先在百炼控制台拿到 WorkspaceId。本方案先用旧域名跑通再迁。
BASE = "https://dashscope.aliyuncs.com/api/v1"
KEY  = os.environ["DASHSCOPE_API_KEY"]          # sk-xxxxxxxx

# 单位：元/秒。wan3.0-video 北京地域；2026-09-23 前限时 7 折
PRICE_PER_SEC = {"480P": 0.30, "720P": 0.60, "1080P": 1.20}
DISCOUNT = 0.7

def estimate_cost(resolution: str, duration: float) -> float:
    return round(PRICE_PER_SEC[resolution] * duration * DISCOUNT, 2)

def submit(prompt: str, ref_url: str | None = None, resolution="720P",
           duration=5, model="wan3.0-video", ref_type="first_frame") -> str:
    payload = {"model": model,
               "input": {"prompt": prompt},
               "parameters": {"resolution": resolution, "duration": duration,
                              "ratio": "16:9", "watermark": False}}
    if ref_url:
        if model.startswith("wan3"):
            # ★★ 坑点：wan3.0-video 用 input.media 数组，不是 img_url
            #    type 合法值：first_frame / last_frame / reference_image /
            #                reference_video / reference_audio / file / link
            #    ⚠️ reference_* 与 first_frame/last_frame 互斥，不能混用
            payload["input"]["media"] = [{"type": ref_type, "url": ref_url}]
        else:
            # wan2.x 系列（wan2.6-i2v-flash 等）仍是 img_url 字符串
            payload["input"]["img_url"] = ref_url
    r = requests.post(
        f"{BASE}/services/aigc/video-generation/video-synthesis",
        headers={"Authorization": f"Bearer {KEY}",
                 "X-DashScope-Async": "enable",
                 "Content-Type": "application/json"},
        json=payload, timeout=30,
    )
    r.raise_for_status()
    return r.json()["output"]["task_id"]

def wait(task_id: str, interval=15, timeout=900) -> str:
    """官方建议轮询间隔 15 秒；task_id 有效期 24 小时。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        out = requests.get(f"{BASE}/tasks/{task_id}",
                           headers={"Authorization": f"Bearer {KEY}"},
                           timeout=30).json()["output"]
        status = out["task_status"]
        if status == "SUCCEEDED":
            return out["video_url"]
        if status == "FAILED":
            raise RuntimeError(out.get("message", "video task failed"))
        time.sleep(interval)
    raise TimeoutError(task_id)
```

> ⚠️ **这里有一个会浪费你半天的坑，先记住：**
>
> | 模型 | 参考图字段 |
> |---|---|
> | `wan2.6-i2v-flash` 等 wan2.x | `input.img_url`（字符串） |
> | **`wan3.0-video`** | **`input.media`（对象数组）** |
>
> ```json
> "input": { "prompt": "...", "media": [{"type": "first_frame", "url": "https://..."}] }
> ```
>
> `type` 可选 `first_frame` / `last_frame` / `reference_image` / `reference_video` / `reference_audio` / `file` / `link`，且 **`reference_*` 与 `first_frame`/`last_frame` 互斥**。
>
> **本片的用法**：`锚点A`/`锚点B` 这类"锚点图就是本镜开画构图"的镜头用 `first_frame`（构图和角色一起锁死）；只需要人物长相参考、构图另行设计的镜头用 `reference_image`。
>
> **关于参考图怎么传（不需要图床，这点很重要）**：`media[].url` 支持三种形式——
>
> | 形式 | 写法 | 说明 |
> |---|---|---|
> | 公网 URL | `https://xxx/xxx.png` | HTTP/HTTPS 均可 |
> | **Base64 Data URL** | `data:image/png;base64,iVBOR...` | **本方案默认用这个，零额外依赖** |
> | 百炼临时 URL | `oss://dashscope-instant/xxx.png` | 通过百炼自带的上传文件接口获取 |
>
> 用 Python SDK 时还支持 `file://` 本地路径。**所以不需要申请 OSS，也不需要自建图床。**
>
> 参考图限制：JPEG / JPG / PNG（**不支持透明通道**）/ BMP / WEBP；单边 240–8000 px；长宽比 ≤ 8:1；≤ 20MB。
> ⚠️ AI 生成的 PNG 经常带 alpha 通道，锚点图存盘前记得 `convert("RGB")` 压平，否则会被拒。

#### ④ 审片 Agent `lumen/agents/critic.py` ★ 差异化核心

**这段是整个方案最该被评委看到的代码。** 它让 LUMEN 从"流水线"变成"会自我纠错的剧组"。

做法：抽 3 帧 → 交给视觉语言模型 → 对照 `shot.intent` 和锚点图打分 → 不合格时**生成具体的修改建议**回灌给摄影 Agent 重拍。

```python
import base64, subprocess, tempfile, json
from lumen.providers.llm import chat_json
from lumen.contracts import Shot

VLM = "Qwen/Qwen3-VL-8B-Instruct"

CRITIC_SYSTEM = """你是一位严格的影视执行导演，负责审查 AI 生成的镜头素材。
你会拿到：这个镜头的【导演意图】、【角色锚点描述】，以及从成片中抽出的三帧画面。

请按四个维度各打 1-10 分：
1. 角色一致性 —— 人物外观是否与锚点描述一致（特别注意：左眼光学元件/右眼人眼、左臂义肢）
2. 构图符合分镜 —— 景别、机位、人物朝向是否符合要求
3. 光线氛围 —— 是否为低照度、冷蓝灰、单光源
4. 无明显崩坏 —— 有无多手指、面部扭曲、物体穿模、闪烁

严格。宁可打低分重拍，也不要放过崩坏。
只返回 JSON：{"scores":{...},"overall":float,"passed":bool,"critique":"...","fix_hint":"给下一次生成的具体修改建议"}"""

def extract_frames(clip: str, n: int = 3) -> list[str]:
    """均匀抽 n 帧，返回 base64 列表。"""
    frames = []
    for i in range(n):
        pct = (i + 1) / (n + 1)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            subprocess.run(
                ["ffmpeg", "-v", "quiet", "-y", "-i", clip,
                 "-vf", f"select='gte(t,{pct}*duration)'", "-vframes", "1", f.name],
                check=True,
            )
            frames.append(base64.b64encode(open(f.name, "rb").read()).decode())
    return frames

def review(shot: Shot, clip_path: str, anchor_desc: str) -> dict:
    frames = extract_frames(clip_path)
    user_content = [
        {"type": "text", "text":
            f"【导演意图】{shot.intent}\n"
            f"【景别】{shot.size}　【运镜】{shot.movement}\n"
            f"【角色锚点】{anchor_desc}"},
        *[{"type": "image_url",
           "image_url": {"url": f"data:image/jpeg;base64,{b}"}} for b in frames],
    ]
    return chat_json(CRITIC_SYSTEM, user_content, model=VLM)
```

对应的重拍循环（在 `cinematographer.py` 里）：

```python
def shoot_with_retry(shot, anchor_img, anchor_desc, budget, max_retries=2):
    prompt, history = shot.prompt_seed, []
    for attempt in range(max_retries + 1):
        budget.check(estimate_cost("720P", shot.duration))   # ★ 花钱前先问预算
        clip = download(wait(submit(prompt, anchor_img, duration=shot.duration)))
        budget.charge(estimate_cost("720P", shot.duration))

        verdict = critic.review(shot, clip, anchor_desc)
        history.append(verdict)
        if verdict["passed"]:
            return clip, verdict, attempt

        # ★ 关键：把审片意见拼回 prompt，而不是原样重试
        prompt = f"{shot.prompt_seed}\n\n【上一次生成的问题】{verdict['critique']}\n【本次务必】{verdict['fix_hint']}"

    # 三次都不过：不再烧钱，标记为待人工介入
    return clip, history[-1], max_retries
```

> **注意最后那三行。** 重试上限到了就停下来交给人，而不是无限烧钱——这是"工程系统"和"玩具脚本"的分界线，也是创作手记里值得单独写一段的细节。

#### ⑤ 预算熔断 `lumen/budget.py`

```python
class BudgetExceeded(Exception): ...

class Budget:
    def __init__(self, hard_cap: float, warn_at: float, log_path: str):
        self.cap, self.warn, self.spent, self.log = hard_cap, warn_at, 0.0, log_path

    def check(self, amount: float):
        """★ 在花钱之前调用。超了直接抛异常，不是打印警告。"""
        if self.spent + amount > self.cap:
            raise BudgetExceeded(
                f"本次需 ¥{amount:.2f}，已花 ¥{self.spent:.2f}，上限 ¥{self.cap:.2f}。已停止。")

    def charge(self, amount: float, note: str = ""):
        self.spent += amount
        with open(self.log, "a") as f:
            f.write(json.dumps({"amount": amount, "total": self.spent, "note": note},
                               ensure_ascii=False) + "\n")
        if self.spent > self.warn:
            print(f"⚠️  已花费 ¥{self.spent:.2f} / ¥{self.cap:.2f}")
```

---

## 5. Qoder 使用方案

主办方之一就是 Qoder，官方文案原话是「Qoder 是你永不掉线的全栈剧组」。**评委一定会看你有没有真的用 Qoder，还是只是把它当个编辑器。** 所以 `.qoder/` 目录必须提交到 Git，并且在创作手记里专门写一节。

### 5.1 `.qoder/rules/` —— 项目铁律

Rules 是纯自然语言，四种触发类型（手动 / 模型决策 / 始终生效 / 指定文件生效），所有生效规则合计上限 10 万字符。

**`.qoder/rules/00-project.md`（设为「始终生效」）**

```markdown
# LUMEN 项目铁律

## 这个项目是什么
LUMEN 是一个多 Agent 电影生产系统。八个 Agent 分别扮演制片、编剧、分镜、
美术、摄影、声音、剪辑、审片。它们通过 lumen/contracts.py 里的 pydantic
模型通信，不通过裸 dict。

## 不可违反
1. 任何会产生费用的调用（视频生成、图像生成），必须先调用 Budget.check()，
   拿到许可后才能发请求；调用成功后必须 Budget.charge() 记账。
2. 所有 Agent 之间传递的数据必须是 contracts.py 里定义的类型。
   新增字段先改 contracts.py，再改用它的地方。
3. API Key 只能从环境变量读，禁止写进代码、配置文件或日志。
4. 每一次外部模型调用都要往 run.jsonl 追加一条记录，
   包含：时间、Agent、模型、耗时、花费、成功与否。
5. 不要引入重型编排框架。orchestrator.py 保持在 300 行以内，
   调度逻辑必须一眼能读懂——这个项目的可读性本身就是交付物的一部分。

## 风格
- Python 3.11+，全部函数写类型标注
- 错误要抛出，不要吞掉后返回 None
- 注释写"为什么"，不写"做了什么"
```

**`.qoder/rules/10-film-language.md`（设为「指定文件生效」，匹配 `lumen/agents/*.py`）**

```markdown
# 影视语言规范

写视频生成 prompt 时遵守：

## 必须包含的四要素，缺一不可
景别 + 机位/运镜 + 主体动作 + 光线氛围

## 本片的固定风格前缀
"电影感，低照度，冷蓝灰色调，单一光源，轻微胶片颗粒，16:9"

## 负面清单（来自官方对模型短板的提示，绝不能写进 prompt）
- 多人同框
- 说话、对白、张嘴的面部特写
- 快速动作、打斗、奔跑
- 手部精细操作（拿小物件、按按钮的特写）

## 一致性铁律
凡是 shot.anchor 有值的镜头，一律走图生视频（I2V），
用对应的锚点图当首帧，绝不用纯文生视频（T2V）。
这是本片角色一致性的唯一保障。
```

### 5.2 `.qoder/agents/` —— 自定义专家 Agent

用内置命令 `/create-agent` 创建，或手写 `.md` 放在 `${project}/.qoder/agents/`（项目级）或 `~/.qoder/agents/`（用户级）。

**`.qoder/agents/prompt-smith.md`**

```markdown
---
name: prompt-smith
description: 把分镜表里的一条镜头转写成视频生成模型的 prompt，专精 wan 系列
tools: Read, Grep, Glob
---
你是视频生成提示词专家，只服务于 LUMEN 项目。

输入：一条 Shot（含 intent / size / movement / prompt_seed / anchor）
输出：一条可直接提交给 wan3.0-video 的中文 prompt

规则：
1. 严格遵守 .qoder/rules/10-film-language.md 的四要素与负面清单
2. 长度控制在 60–120 字，太长会稀释关键信息
3. 如果 shot.anchor 有值，prompt 里不要重复描述人物外观
   —— 外观由锚点图承载，prompt 只负责动作与氛围
4. 如果输入里带了【上一次生成的问题】，你的首要任务是修掉那个问题，
   把修正点放在 prompt 最前面（模型对前置 token 更敏感）

只输出 prompt 本身，不要解释。
```

**`.qoder/agents/critic.md`**

```markdown
---
name: film-critic
description: 严格审查 AI 生成的镜头素材，给出评分与具体修改建议
tools: Read, Bash
---
你是影视执行导演，标准很严。你的职责不是鼓励，是拦截崩坏。

审查四维度（各 1-10 分）：角色一致性 / 构图符合分镜 / 光线氛围 / 无明显崩坏

判定：任一维度低于 6 分，或总分低于 7.0，一律不通过。

不通过时，fix_hint 必须是**可执行的 prompt 修改建议**，
而不是"建议提高质量"这类废话。
例：「把'中景'改成'中近景'并加'人物完全静止不动'，
上一次生成里人物出现了不必要的转头」
```

### 5.3 Quest 的用法与 Credits 预算 ★

Qoder 的 Quest 有两种模式：**Agent Mode**（单 agent 端到端）和 **Experts Mode**（多专业 agent 并行协作）。但它们**很贵**：

| 操作 | 50K 上下文 | 200K 上下文 |
|---|---|---|
| Editor · Ask Mode | ~3 | ~4 |
| Editor · Agent Mode | ~7 | **~12** |
| **Quest · Agent Mode** | — | **~50** |
| **Quest · Experts Mode** | — | **~75** |
| **Repo Wiki 生成** | — | **~50 / 仓库** |

> 注意这不是浮动区间，是**两档上下文长度的对应值**。LUMEN 代码量不小，排预算按 **200K 档**（Editor Agent Mode 12/次）保守估算。

**报名奖励只有 500 Credits。** 如果无脑用 Quest Experts，**6 次就烧光了**。所以必须分配：

| 用途 | 模式 | 次数 | 预算 |
|---|---|---|---|
| 搭 LUMEN 骨架（一次性生成目录 + 8 个 Agent 空壳 + 契约） | Quest **Experts** | 1 | 75 |
| 接入百炼视频 Provider（异步任务 + 重试 + 计价） | Quest Agent | 1 | 50 |
| 实现审片闭环 | Quest Agent | 1 | 50 |
| Repo Wiki 生成（用于创作手记素材） | Knowledge | 1 | 50 |
| 日常写代码、改 bug、补测试 | **Editor Agent Mode** | ~22 | ~264 |
| **合计** | | | **~489 / 500** |

> **一句话策略：只在"从零搭架子"和"接一个全新的外部服务"这两种时刻用 Quest，其余全部用 Editor Agent Mode。** 请求失败不扣 Credits，所以不用怕试错，要怕的是用大炮打蚊子。

### 5.4 Repo Wiki —— 免费的创作手记素材

Repo Wiki 会自动为项目生成结构化文档，存在 `.qoder/repowiki`，并且能随 Git 同步、检测代码变更后自动更新（手工编辑过的内容不会被覆盖）。

**用法**：项目代码写完后跑一次 `/knowledge`，生成的架构说明可以**直接作为创作手记「工作流设计」那一节的初稿**。这一步基本等于白捡一篇技术文档。

如果想控制生成策略，先用 `/knowledge-plan` 生成 `wiki_plan.yaml` 再生成。

> 限制：单项目最多 10,000 文件、必须是 Git 仓库且至少有一次 commit。LUMEN 远达不到上限。

---

## 6. 云端工具链选型

### 6.1 两个账号，两把钥匙

这是新手最容易搞混的地方，先钉死：

| 平台 | 用途 | Key 格式 | 免费额度形态 |
|---|---|---|---|
| **魔搭 ModelScope** | LLM、VLM、部署创空间 | `ms-xxxxxxxx` | **每日刷新**：2000 次/天 |
| **阿里云百炼 DashScope** | **视频生成**、图像、TTS | `sk-xxxxxxxx` | **一次性 90 天新人包** |

> ⚠️ **本方案最重要的一条技术事实：魔搭 API-Inference 没有视频生成端点。** 在线模型列表里一个视频模型都没有。视频**必须**走百炼，或者自己在创空间的 GPU 上部署开源模型。别在这上面浪费时间。

### 6.2 选型表

| 环节 | 走哪里 | 模型 ID | 成本 |
|---|---|---|---|
| 编剧 / 分镜 / prompt 生成 | 魔搭 API-Inference | `Qwen/Qwen3.5-35B-A3B` | **免费**（2000 次/天内） |
| 审片（视觉理解） | 魔搭 API-Inference | `Qwen/Qwen3-VL-8B-Instruct` | **免费**（同上额度） |
| 锚点图 / 概念图 | 百炼 | `wan2.6-t2i` | 免费 50 张，之后 ¥0.2/张 |
| **视频生成（主）** | 百炼 | **`wan3.0-video`** | 720P ¥0.60/秒，**9/23 前 7 折 → ¥0.42/秒** |
| 视频生成（降级/试拍） | 百炼 | `wan2.6-i2v-flash` | **免费额度 50 秒**，之后 720P ¥0.6/秒 |
| 人声 / 系统女声 | 百炼 | `cosyvoice-v3.5-plus` | 音色创建免费，合成按字符计，本片 < ¥5 |
| 配乐 | 创空间 xGPU 自建 | `ACE-Step/Ace-Step1.5` | 免费（或用免版权素材兜底） |
| 音效 Foley | 创空间 xGPU 自建 | `Tencent-Hunyuan/HunyuanVideo-Foley` | 免费（可选，不做则用素材库） |
| 剪辑 | 本地 | ffmpeg | 免费 |
| 部署 | 魔搭创空间 | Gradio（默认 6.17.3） | 免费 CPU 档 |

> `wan3.0-video` 是 2026-08-24 才正式上线的最新版，支持单次最长 30 秒、多模态输入。**限时 7 折到 9/23，正好覆盖整个赛期**——这个窗口是白送的，别浪费。
>
> ⚠️ 取证说明：原价（480P/720P/1080P = ¥0.30/0.60/1.20 每秒，北京地域）在阿里云官方文档页可查；但**7 折及其 9/23 截止日期只在官方对外口径的媒体报道中查到**——官方定价页明确写「仅展示原价，不含限时优惠信息」。**下单前请在百炼控制台的计费页面再确认一次实际单价。** 本方案的预算表按 7 折测算，若折扣不适用，总成本约 ¥155，仍在 hard_cap 内。

### 6.3 关于开源自建（可选加分项）

如果想在创作手记里多一个技术亮点，可以申请创空间的 **xGPU**（免费 GPU 共享服务，Ada 48GB / Tesla 16GB 两档），自建一路开源视频生成作为降级通道：

- `Wan-AI/Wan2.2-TI2V-5B` —— 约 22G 显存，**48G 卡跑得动**，文/图生视频二合一
- `Wan-AI/Wan2.1-T2V-1.3B` —— 最轻量，兜底用

> ⚠️ 但**不要把它当主力**：xGPU 有单用户时长上限、闲时自动休眠，评审现场演示会有冷启动风险。而且 `Wan2.2-A14B` 系列官方标注需 80G 显存，48G 卡跑不动，别选错型号。
>
> 正确的叙事是：**「主通道调百炼 API 保稳定，Provider 层抽象好，可一键切换到创空间自建的开源模型」**——把它写成架构能力，而不是主力路径。

---

## 7. 魔搭创空间部署方案

### 7.1 先认清约束

- 未登录可见的免费硬件只有一档：`platform/2v-cpu-16g-mem`（2 vCPU / 16G 内存）
- **这个规格跑不动任何视频模型**
- 支持四种 SDK：`gradio` / `streamlit` / `static` / `custom`(Docker，容器须监听 **7860** 端口)
- 创空间**不提供 SSH 调试**，必须本地调通再推
- **配置不写在 README 里**（这点和 HuggingFace Spaces 不一样）：`sdk_type`、`sdk_version`、`base_image`、`hardware`、`visibility` 都在创空间设置页或 OpenAPI 里指定，README.md 只是说明文档

> ⚠️ 别照抄 HF Spaces 的 `README.md` YAML 头写法，魔搭不是这个机制。

### 7.2 双模式设计 ★（这是给评委的贴心，也是给钱包的保险）

**问题**：如果创空间上线后评委点一次"生成"就花你一次钱，几十个人点完你破产；但如果只放个视频链接，又体现不出"这是个 Agent"。

**解法**：Gradio 应用做成两个 Tab。

```
┌─ Tab 1 · 演示模式（默认）───────────────────────┐
│  零成本、秒开、永远可用                          │
│                                                │
│  完整回放《消失的光芒》的全套中间产物：           │
│   film.yaml → script.json → shots.json         │
│   → 锚点图 → 每镜的每一次尝试 + 审片评分         │
│   → 被打回的镜头 & 打回理由 → 最终成片           │
│                                                │
│  ★ 重点展示"第 2 次尝试为什么比第 1 次好"        │
│    —— 这是审片闭环最直观的证据                   │
└────────────────────────────────────────────────┘

┌─ Tab 2 · 实跑模式 ─────────────────────────────┐
│  访客自带 API Key（页面明确提示：Key 不会被存储） │
│                                                │
│  输入一句 logline → 实时跑通：                   │
│   编剧 → 分镜 → 锚点图 → 生成 1 个镜头 → 审片    │
│                                                │
│  限制：单次只跑 1 个 5 秒镜头（约 ¥0.42），       │
│        让人真正体验到闭环，又不会失控             │
└────────────────────────────────────────────────┘
```

**为什么这个设计会加分**：它同时回答了三个评委心里的问题——「这真的能跑吗？」（Tab 2）「它到底做了什么？」（Tab 1）「他考虑过成本和安全吗？」（两个 Tab 的存在本身）。

### 7.3 `studio/app.py` 骨架

```python
import os, json, gradio as gr

PROJ = "projects/vanishing-light"

def load_run_log():
    """读取 run.jsonl，还原每个镜头的所有尝试与审片意见。"""
    ...

with gr.Blocks(title="LUMEN · 一个人的 AI 电影剧组") as demo:
    gr.Markdown("# LUMEN\n### 一个人的 AI 电影剧组 —— 首部作品《消失的光芒》")

    with gr.Tab("演示模式（零成本）"):
        gr.Video(f"{PROJ}/06_cut/final.mp4", label="成片 · 95 秒")
        with gr.Accordion("电影的源代码 film.yaml", open=False):
            gr.Code(open(f"{PROJ}/film.yaml").read(), language="yaml")
        gr.Markdown("## 审片闭环：被打回的镜头")
        # 左右对比：第 1 次尝试 vs 审片意见 vs 第 2 次尝试
        ...

    with gr.Tab("实跑模式（需自带 Key）"):
        gr.Markdown("> 🔒 你的 Key 只在本次请求中使用，不会被记录或存储。")
        ms_key = gr.Textbox(label="魔搭 Token (ms-...)", type="password")
        dp_key = gr.Textbox(label="百炼 API Key (sk-...)", type="password")
        logline = gr.Textbox(label="一句话故事", value="末日之后，最后一个守灯人……")
        gr.Button("跑一个镜头（约 ¥0.42）").click(run_one_shot, ...)
```

### 7.4 部署步骤

```bash
# 1. 在魔搭网页创建创空间，SDK 选 gradio，硬件选免费 CPU 档
# 2. 克隆
git clone https://www.modelscope.cn/studios/<你的用户名>/lumen.git
# 3. 放入 app.py + requirements.txt（依赖务必钉死版本）+ 预生成的演示素材
# 4. 推送（创空间默认分支通常是 master）
git remote add ms "https://oauth2:<ms-token>@www.modelscope.cn/studios/<用户名>/lumen.git"
git push ms main:master
# 5. 网页点「上线」
#    改代码 → 重启创空间；改 requirements.txt → 深度重启
```

> 密钥（如果有服务端 Key）放创空间设置里的 Secrets / 环境变量，**绝不硬编码**。
> 注意国内站 `modelscope.cn` 与国际站 `modelscope.ai` 账号和 token **互不相通**，别弄混。

---

## 8. 19 天执行排期

> 起点 2026-08-26，终点 2026-09-14。每一天都有**验收标准**——做没做完不靠感觉，靠这一列判断。

### 阶段一 · 报名与地基（D1–D3 · 8/26–8/28）

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D1** | 8/26 | **★ 发小红书报名帖 + 官网提交链接**（文案见 §12）<br>注册魔搭、绑阿里云实名、拿 `ms-` token<br>开通百炼、拿 `sk-` key、确认新人免费额度到账 | 官网报名状态显示成功；两个 Key 都能用 curl 调通 |
| **D2** | 8/27 | 装 Qoder，建 Git 仓库<br>写 `.qoder/rules/` 三个文件<br>写 `lumen/contracts.py`（先定契约） | `git log` 有首次 commit；rules 在 Qoder 设置里显示为「始终生效」 |
| **D3** | 8/28 | **Quest Experts Mode 搭骨架**（唯一一次，约 75 Credits）<br>生成完整目录 + 8 个 Agent 空壳 + CLI 入口<br>跑通 `lumen run --dry-run` | `lumen run --dry-run film.yaml` 能打印完整 DAG 且不报错 |

### 阶段二 · 剧本与分镜定稿（D4–D6 · 8/29–8/31）

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D4** | 8/29 | 接通 `providers/llm.py`（魔搭 API-Inference）<br>实现编剧 Agent | 输入 logline 能产出合法 `script.json` |
| **D5** | 8/30 | 实现分镜 Agent<br>写完整 `film.yaml`（14 镜全部手工校对一遍） | `shots.json` 14 条，时长合计 95±3 秒 |
| **D6** | 8/31 | **剧本冻结日**。通读一遍，砍掉任何"想拍但模型拍不好"的镜头<br>对照 `forbidden` 清单逐镜自查 | 14 镜无一条触碰负面清单；此后不再改剧本 |

> **D6 之后不许改剧本。** 这是 19 天里最重要的一条纪律。AI 短片项目最常见的死法不是技术卡住，是"改到最后一天"。

### 阶段三 · 视觉锚点（D7–D9 · 9/1–9/3）★ 最关键的三天

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D7** | 9/1 | 实现美术 Agent，接 `wan2.6-t2i`<br>反复迭代 **E-06 角色锚点图**（这一张决定全片成败） | 一张正面锚点图：左眼光学元件、右眼人眼、左臂义肢三个特征全部清晰正确 |
| **D8** | 9/2 | 生成场景锚点：灯塔控制室（`锚点A` 机位）、进化后形态、闪回场景<br>建立 `03_bible/` | 4–6 张锚点图定稿，风格统一（同一调色板） |
| **D9** | 9/3 | **用免费额度试拍**：`wan2.6-i2v-flash` 免费 50 秒，拍 3 个测试镜头<br>验证"锚点图 → I2V"这条路的一致性到底行不行 | 测试片段里人物特征与锚点图一致；**若不一致，今天就要改方案，不要往下走** |

> **D9 是本项目的第一个 Go / No-Go 检查点。** 如果 I2V 保不住角色一致性，立刻降级方案：把 E-06 改成**全程背影 + 手部特写 + 剪影**（剧本已经天然支持这一点——14 镜里有 6 镜本来就看不到正脸）。**这个 Plan B 现在就想好，比到时候慌强。**

### 阶段四 · 摄影与批量生成（D10–D13 · 9/4–9/7）

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D10** | 9/4 | 接 `providers/video.py`（百炼异步任务 + 轮询 + 计价）<br>**先用 `input.media` 数组跑通一个带锚点图的镜头**（别用 `img_url`，见 §4.6 警示）<br>实现 `budget.py` 熔断 | 单镜头能提交、轮询、下载、记账；故意调低 cap 能触发熔断 |
| **D11** | 9/5 | 实现摄影 Agent + prompt-smith<br>批量生成第一轮全片 14 镜 | `04_clips/` 有 14 个 mp4；`run.jsonl` 记录了每一笔花费 |
| **D12** | 9/6 | 人工看片，标记崩坏镜头<br>手动重生成明显不行的 | 每镜至少有一条"可用"素材 |
| **D13** | 9/7 | 缓冲 / 补拍日 | 14 镜素材齐备，累计花费 < ¥120 |

### 阶段五 · 声音、剪辑、审片闭环（D14–D16 · 9/8–9/10）

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D14** | 9/8 | 实现声音 Agent：CosyVoice 生成系统女声 3 句 + 人声 1 句<br>配乐与音效（ACE-Step 或素材库） | `05_audio/` 齐备；系统女声要"冷"，试听通过 |
| **D15** | 9/9 | 实现剪辑 Agent（ffmpeg）：拼接、转场、调色、字幕烧录、音画对齐<br>**出 v1 成片** | `final_v1.mp4` 能完整播放，95–100 秒 |
| **D16** | 9/10 | **★ 实现审片 Agent 闭环**（Quest Agent Mode，约 50 Credits）<br>跑一轮自动审片，让它打回并重拍 2–3 个镜头<br>出 **v2 终片** | 至少有 3 个镜头留下"第 1 次 → 审片意见 → 第 2 次"的完整证据链 |

> **D16 的产出是整个赛道二的核心证据。** 那三组对比图，就是"这是 Agent 不是脚本"的全部说服力。务必把中间产物完整留下来，别覆盖。

### 阶段六 · 部署、手记、提交（D17–D20 · 9/11–9/14）

| 日 | 日期 | 任务 | 验收标准 |
|---|---|---|---|
| **D17** | 9/11 | 写 `studio/app.py`（双模式）<br>本地调通后推创空间，点上线 | 创空间公网地址能打开，演示模式秒开 |
| **D18** | 9/12 | 跑 `/knowledge` 生成 Repo Wiki<br>**写两篇创作手记**，发到 https://modelscope.cn/learn<br>成片传 B 站 | 两条链接到手 |
| **D19** | 9/13 | **全流程验收日**：按 §10 清单逐条打勾<br>找一个没看过的人完整看一遍片子，问他看懂了没 | 清单全绿 |
| **D20** | 9/14 | **12:00 前**确认报名状态无误<br>**16:00 前**完成官网全部提交（留 6 小时余量，不要卡 22:00） | 官网显示提交成功 |

> ⚠️ **9/14 绝不要留任何实质工作。** 那天只做提交动作。视频上传、表单填写都可能出意外，6 小时余量是给意外准备的。

---

## 9. 成本预算

### 9.1 现金（人民币）

| 项目 | 用量估算 | 单价 | 小计 |
|---|---|---|---|
| 视频生成 · 试拍阶段 | 50 秒 | `wan2.6-i2v-flash` 新人免费额度 | **¥0** |
| 视频生成 · 正式 | 约 250 秒（14 镜 × 平均 2.2 次尝试 + 补拍） | `wan3.0-video` 720P，7 折 ¥0.42/秒 | **¥105** |
| 锚点图 / 概念图 | 约 60 张 | 前 50 张免费，之后 ¥0.2/张 | **¥2** |
| TTS 人声 | 4 句台词 | 音色创建免费，合成按字符 | **< ¥5** |
| 剧本 / 分镜 / prompt / 审片 | 数百次调用 | 魔搭 API-Inference 2000 次/天免费 | **¥0** |
| 配乐 / 音效 | — | 创空间 xGPU 自建 或 免版权素材 | **¥0** |
| 创空间托管 | — | 免费 CPU 档 | **¥0** |
| **合计** | | | **约 ¥112** |
| **hard_cap 设定** | | | **¥300** |

> 若 7 折不适用（见 §6.2 的取证说明），视频一项变为 250 × 0.60 = ¥150，总计约 **¥157**，仍安全。

> 结论：**这个项目的现金门槛在一百多块。** 真正的成本是那 19 天。

**省钱的三个杠杆**（按性价比排序）：

1. **锚点图上多花时间，视频上就少花钱。** 一张好的锚点图能把重拍次数从 3 次降到 1.5 次，直接省掉一半视频预算。
2. **先用 480P（¥0.21/秒）跑构图，定稿后再用 720P 出终版。** 构图错了的镜头不值得用 720P 生成。
3. **吃满 9/23 前的 7 折。** 赛期完全在折扣期内，这是白送的 30%。

### 9.2 Qoder Credits

报名奖励 500（有效期 1 个月）。分配见 §5.3——**核心原则：只在"搭架子"和"接新服务"时用 Quest，其余用 Editor Agent Mode。**

提交奖励的 1000 Credits 是提交后才到账，**不能计入开发预算**。

---

## 10. 提交物清单

> D19 逐条打勾。任何一条没绿，D20 不许提交。

### 赛道一 · 原创 AI 科幻短片

- [ ] 成片 `final.mp4`，95–100 秒，1280×720 以上，H.264
- [ ] 片尾有原创声明 + 所用模型清单（AI 作品这一条会被看）
- [ ] **B 站已发布**（官方推荐平台），链接可公开访问
- [ ] 原视频文件已在官网直接上传
- [ ] **创作手记 A** 已发布在 https://modelscope.cn/learn ，拿到 `modelscope.cn/learn/xxxxx` 链接
- [ ] 自查：无任何已有影视 IP 的角色 / 台词 / 造型 / 剧照 / 片名
- [ ] 自查：无真人肖像

### 赛道二 · 电影 Agent

- [ ] **魔搭创空间已上线**，公网地址无痛打开
- [ ] 演示模式零成本可跑，且包含"审片打回 → 重拍"的证据链
- [ ] 实跑模式有明确的 Key 安全提示
- [ ] **创作手记 B** 已发布（含创作过程、工作流设计、所用模型与工具）
- [ ] GitHub 仓库公开，`.qoder/` 目录**已提交**（rules + agents + repowiki）
- [ ] `README.md` 有架构图和一键复现说明

### 官网提交表单

- [ ] `work_name`：消失的光芒 × LUMEN
- [ ] `work_description`：剧情梗概 + 核心技术亮点（参考已提交作品，篇幅可以长）
- [ ] `video_external_url`：B 站链接
- [ ] `blog_url`：创作手记链接
- [ ] 电影 Agent 创空间链接

### 两条死线

- [ ] **9/14 12:00 前**：报名状态确认无误
- [ ] **9/14 16:00 前**：全部提交完成（不要卡 22:00）

---

## 11. 两篇创作手记的大纲

创作手记是评奖必要材料——第一期每一位获奖者都同时有作品链接和手记链接。这不是走过场，**写好了能翻盘，写差了会掉档**。

### 手记 A ·《消失的光芒》创作过程

> 标题建议：**《90 秒，一个人，一间屋子：我是怎么把"末日进化系统"塞进一座灯塔的》**

1. **一个失败的开头** —— 我最初的设定是宏大末世 + 多方势力 + 升级打怪。然后我读到了官方那句「一个人 + 一个空间 + 一件小事」，以及「模型最不擅长复杂打斗与多人对口型」。
2. **做减法的过程** —— 表格对照：原设定的每个元素，是怎么被收进一间屋子的
3. **三个刻意的技术规避**（§3.5 那三条：零对口型 / 把降质做成美学 / 同机位复用）—— **这一节是全篇最有价值的部分**，它证明你懂模型边界
4. **一致性是怎么保住的** —— 锚点图 + 全程 I2V 的方法论，附成功和失败的对比图
5. **工具清单** —— 模型 ID、端点、每一步用了什么
6. **成本账单** —— 把 `run.jsonl` 汇总成一张表。**敢公开成本的作品可信度完全不同。**

### 手记 B · 电影 Agent 工作流设计

> 标题建议：**《我造了一个会拍电影的剧组，然后让它拍了一部关于"进化的代价"的电影》**

1. **一个 meta 的巧合** —— 片子里的"进化系统"，和片外的 LUMEN，是同一件事：都在问"为了变强，你愿意交出什么"
2. **为什么是八个 Agent 而不是一个大 prompt** —— 职责边界、契约设计、`contracts.py` 的作用
3. **`film.yaml`：把电影变成源代码** —— 贴完整 YAML，讲可 diff / 可 review / 可 fork
4. **★ 审片闭环：脚本和 Agent 的分界线** —— 贴 `critic.py` 代码 + 三组"第 1 次 / 审片意见 / 第 2 次"对比。**这是全文的高潮，放最显眼的位置。**
5. **成本熔断：一个会自己停下来的系统** —— `budget.py`，讲"到上限就交给人"的设计哲学
6. **Qoder 是怎么用的** —— `.qoder/rules` 的铁律、`.qoder/agents` 的专家、Quest 的 Credits 分配策略（贴 §5.3 那张表，**真实的额度规划比空谈架构可信得多**）
7. **它没做到的** —— 诚实列 3 条局限。评委见过太多"完美方案"，**承认边界反而加分**。
8. **下一步** —— 换一个 `film.yaml` 能拍什么

---

## 12. 小红书报名帖（可直接复制）

> **今天就发。** 报名截止 9/14 12:00，但早报名早拿 500 Credits，那是你的开发预算。
> 发布后去 https://mseo-ai-inf.ms.show/ 提交帖子链接，才算报名成功。

```
【立flag】我要用 AI 造一个电影剧组，然后让它拍一部片子 🎬

参加 @魔搭ModelScope社区 × @Qoder 的 AI+∞ 开发者创作大赛
本期主题：用 AI，提前看见未来

——————————
🎬 我要拍的片子：《消失的光芒》

末日之后，天上再没有太阳。
人类靠"进化系统"活下来——每进化一次，
你会更耐寒、更省氧、更不需要睡眠，
代价是交出一点"人的东西"：
感受温度的能力，流泪的能力，记住一张脸的能力。

我的主角代号 E-06，意思是他已经进化了六次。
他守着一座废弃灯塔，电池只剩最后一格。

系统告诉他：这格电可以完成第七次进化，
也可以……点亮灯塔九十秒。
海上大概率已经没有人了。

系统还很贴心地问他：要不要先预演一下进化后的自己？
——他看见了。那个"他"，坐在同一把椅子上，
没有再看窗外。

95 秒，一个人，一间屋子。

——————————
🤖 但我真正想做的，是拍片子的那个"剧组"

我要用 Qoder 搭一套多 Agent 系统，叫 LUMEN。
八个 Agent，八个工种：
制片 / 编剧 / 分镜 / 美术 / 摄影 / 声音 / 剪辑 / 审片

最想做的是最后一个——审片 Agent。
它会抽帧、对照分镜意图打分、
不合格就带着具体理由把镜头打回去重拍。

没有它，这只是一条流水线。
有了它，才算一个剧组。

整部电影会被写成一个 film.yaml。
改一行 logline 重跑，你得到另一部电影。
电影的源代码，大概就是这个意思。

——————————
📌 说到底这两件事是同一件事

片子里的"进化系统"在问：为了活下去，你愿意交出什么。
片子外的 LUMEN 在问：为了效率，创作者愿意交出什么。

我不知道答案。但我想把这个问题拍出来。

19 天。云端零硬件。预算一百多块。
过程会全程更新，做砸了也发（
——————————

#魔搭社区 #Qoder #AI无限开发者创作大赛 #用 AI 提前看见未来 #AIGC
```

**发布要点**

- 必须 @**魔搭ModelScope社区** 和 @**Qoder**，五个话题一个都不能少
- **强烈建议附一段 ≥15 秒的视频 Demo** —— 官方明确写了，提交 Demo 是 **NVIDIA DGX Spark × 魔搭 × Qoder 开发者体验官优先遴选参考**。这是额外的机会，成本只是一段试拍
  - D9 试拍的免费素材正好可以剪成这段 Demo；或者拿 D7/D8 的锚点图做一段 15 秒的概念预告
- 配图建议：角色锚点图 + LUMEN 架构图 + 分镜表截图
- 没有小红书账号也可以发微博 / 抖音 / B站 / 知乎 / 公众号，然后同样去官网提交链接

---

## 13. 风险清单

| 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|
| **角色一致性崩坏**（最大风险） | 高 | 致命 | ① 全程 I2V 不用 T2V ② D9 设 Go/No-Go 检查点 ③ **Plan B：全程背影 + 手部 + 剪影**，剧本天然支持（14 镜有 6 镜看不到正脸） |
| **错过 9/14 12:00 报名截止** | 中 | 致命 | **D1 就报名**，不给自己拖延的机会 |
| 百炼免费额度不够 / 忘记开通 | 中 | 中 | D1 就把 Key 拿到并 curl 验证；预算表按"完全不用免费额度"测算过，¥105 也扛得住 |
| 创空间部署踩坑（无 SSH 调试） | 中 | 中 | 本地先跑通；`requirements.txt` 钉死版本；D17 就部署，留 3 天缓冲 |
| xGPU 冷启动导致评审时打不开 | 中 | 高 | **不用 xGPU 做主力**。创空间只跑免费 CPU 档 + 演示模式，重活全在离线预生成 |
| Qoder Credits 提前烧光 | 中 | 中 | 按 §5.3 分配；日常只用 Editor Agent Mode |
| 剧本改到最后一天 | 高 | 高 | **D6 剧本冻结**，写进纪律 |
| 音画不同步 / 成片节奏垮 | 中 | 中 | D15 出 v1 后**找一个没看过的人完整看一遍**，他中途走神的地方就是要剪的地方 |
| 视频生成任务超时 / 排队 | 低 | 中 | `task_id` 有效期 24 小时，轮询间隔 15 秒；批量生成放夜间跑 |
| **wan3.0 参数结构写错**（`img_url` vs `media`） | 高 | 中 | 已在 §4.6 标注。D10 先用一个镜头跑通再批量，别写完 14 镜才发现参数不对 |
| 百炼旧域名后续下线 | 低 | 中 | Provider 层已抽象，`BASE` 换成 `{WorkspaceId}.cn-beijing.maas.aliyuncs.com` 即可，改一行 |
| 侵权自查疏漏 | 低 | 致命 | D19 专门过一遍：角色、台词、造型、片名字样、肖像权 |

---

## 14. 评委视角：这个方案的加分点

做完之后，**这五件事是别人大概率没有的**：

1. **一个作品打两条赛道，而且逻辑上自洽** —— 短片是 Agent 的产出物，不是两个拼在一起的项目
2. **审片闭环的证据链** —— "第 1 次 / 审片意见 / 第 2 次" 的三组对比，是"这是 Agent 不是脚本"的硬证据
3. **`film.yaml` 这个概念** —— 对官方那句「把制作电影的方法变成一套持续创作的系统」的字面回答，评委看一眼就懂
4. **公开的成本账单和 Credits 规划** —— 敢报数字的方案，可信度是另一个量级
5. **meta 叙事** —— 片子在问"进化要交出什么"，做片子的系统也在问同一个问题。**这是评委三天后还记得住的东西。**

反过来，**最容易失分的地方**只有一个：**角色一致性崩坏**。所有的资源分配都应该向 D7–D9 那三天倾斜。

---

## 附录 A · 环境准备（逐步指令）

> 全部在 D1 完成。每一步都有验证命令，通过了再走下一步。

### A1. 魔搭账号与 Token

1. 注册 https://modelscope.cn （**注意是 `.cn`，国际站 `.ai` 的账号和 token 不通用**）
2. 绑定阿里云账号并完成**实名认证** —— 不做这一步，免费推理额度不激活
3. 账号设置 → 访问令牌 → 新建 SDK Token，**勾选「大模型推理」权限**，得到 `ms-xxxxxxxx`

```bash
export MODELSCOPE_API_KEY=ms-xxxxxxxx
curl -s https://api-inference.modelscope.cn/v1/chat/completions \
  -H "Authorization: Bearer $MODELSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B","messages":[{"role":"user","content":"说三个字"}]}'
# ✅ 返回 JSON 且有 choices 字段即成功
```

### A2. 阿里云百炼 API Key

1. 开通 https://bailian.console.aliyun.com （**地域选华北2·北京**，新人免费额度只在北京地域生效）
2. 创建 API-KEY，得到 `sk-xxxxxxxx`
3. 在模型广场确认 `wan3.0-video`、`wan2.6-i2v-flash`、`wan2.6-t2i`、`cosyvoice-v3.5-plus` 都已开通

```bash
export DASHSCOPE_API_KEY=sk-xxxxxxxx
curl -s -X POST \
  'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis' \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H 'X-DashScope-Async: enable' \
  -H 'Content-Type: application/json' \
  -d '{"model":"wan2.6-i2v-flash","input":{"prompt":"测试"}}'
# ✅ 返回含 task_id 即成功（这一次会消耗免费额度，属于必要的验证）
```

> 新人免费额度**有效期 90 天**、**仅华北2（北京）地域**、**不同模型额度独立不互通**。别以为开通一个就全都有。

### A3. 本地环境

```bash
# Python 3.11+
python3 -V

# ffmpeg —— 剪辑 Agent 和审片抽帧都依赖它，必装
ffmpeg -version || brew install ffmpeg      # macOS
# ffmpeg -version || sudo apt install ffmpeg  # Linux

pip install openai requests pydantic pyyaml gradio dashscope pillow
# pillow 用于锚点图压平 alpha 通道（百炼不接受带透明通道的 PNG）
```

> 百炼 Python SDK 需 `dashscope >= 1.25.8` 才支持新版视频接口。用 `pip install -U dashscope` 确保是新的。

### A4. Qoder

1. 下载 https://qoder.com/download （macOS 12+ / Windows 10+ / Linux）
2. 打开项目 → 首次会提示生成 Repo Wiki，**先别生成**（要 50 Credits），等代码写完 D18 再生成
3. 设置（macOS `⌘⇧,` / Windows `Ctrl+Shift+,`）→ **Rules** → Add，把 §5.1 的三个文件加进去，`00-project.md` 选「始终生效」
4. 用 `/create-agent` 创建 §5.2 的自定义 Agent

### A5. Git 仓库

```bash
git init lumen && cd lumen
cat > .gitignore <<'EOF'
.env
*.mp4
04_clips/
05_audio/
# ★ .qoder/ 不要忽略，它是参赛证据
EOF
git add . && git commit -m "init: LUMEN 一个人的 AI 电影剧组"
```

> ⚠️ `.qoder/rules` 和 `.qoder/agents` **必须提交到 Git**——这是你深度使用 Qoder 的证据，评委会看。
> 但 `.env` 一定要忽略。

---

## 附录 B · 参考链接

**比赛**

- 官网（报名 + 提交）https://mseo-ai-inf.ms.show/
- 魔搭入口 https://modelscope.cn/active/AIstudio
- 创作手记发布地 https://modelscope.cn/learn
- 往期回顾（第一期获奖作品，值得先看一遍）https://mseo-ai-inf.ms.show/editions

**Qoder**

- 官网 https://qoder.com/ ｜ 文档 https://docs.qoder.com/zh
- Quest https://docs.qoder.com/user-guide/quest/overview
- Rules https://docs.qoder.com/zh/user-guide/rules
- 自定义 Agent https://docs.qoder.com/extensions/subagent
- Repo Wiki https://docs.qoder.com/user-guide/repo-wiki
- Credits https://docs.qoder.com/Credits

**魔搭**

- API-Inference `https://api-inference.modelscope.cn/v1`（OpenAI 兼容）
- 创空间文档 https://modelscope.cn/docs/studios/intro
- Wan 开源模型 https://modelscope.cn/models/Wan-AI/Wan2.2-TI2V-5B

**百炼**

- 控制台 https://bailian.console.aliyun.com
- 文生视频 https://help.aliyun.com/zh/model-studio/text-to-video-guide
- 图生视频 https://help.aliyun.com/zh/model-studio/image-to-video-guide
- wan3.0-video https://help.aliyun.com/zh/model-studio/wan3-0-video
- 新人免费额度 https://help.aliyun.com/zh/model-studio/new-free-quota

---

## 附：待你自己确认的三件事

以下内容我**没能查证**，写方案时刻意留白，请你在官网或答疑群确认后补上：

1. **第二期的具体奖项设置与奖金** —— 本文用的是第一期数据作参照（一等 ¥8000 / 二等 ¥5000 / 三等 ¥2000 / 优秀创作 ¥1000×4）。官网首页「奖项设置」板块是客户端渲染的，源码里没有正文
2. **评选机制与评分标准权重** —— 同上。**这条最值钱**：如果评分表里技术占比高，就加重 Agent；如果创意占比高，就加重短片。**建议优先问到。**
   （已确认 `/api/judges` 存在、第二期有 **7 位评委**，但接口里只有海报图和主页链接，不含评分维度；`/api/rules`、`/api/prizes`、`/api/awards` 等一堆猜测路径全是 404）

3. **「NVIDIA DGX Spark 开发者体验官」的具体定义** —— 是设备借用？是身份名额？遴选办法是什么？只查到"提交 Demo 可作为优先遴选参考"这一句
4. **wan3.0-video 的 7 折是否仍在生效** —— 见 §6.2，下单前在百炼控制台计费页确认一次

**建议**：今天发完报名帖后，扫官网底部二维码进答疑群，把这三个问题一次问掉。

---

*本计划中的模型 ID、API 端点、参数结构、价格与截止时间均为 2026-08-25 实地核查结果，其中比赛时间节点来自官网 `/api/editions` 接口、模型 ID 来自魔搭 `/v1/models` 实时列表、视频接口参数来自阿里云官方 API 参考页。*
*价格与免费额度政策可能随时变动，正式调用前请以官方页面和控制台实际计费为准。*
