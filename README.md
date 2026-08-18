# HeartMind · AI 关系智能平台

> **Relationship as Project** —— 以项目管理思想管理相亲交往全生命周期的
> AI Relationship Intelligence Platform。

HeartMind 不是恋爱聊天机器人，而是 **AI Relationship CRM + AI Agent 工作台**。
它把每位相亲对象视为一个独立的「关系项目」，用 AI Agent 将聊天、约会、人物信息
整合为不断演化的**关系知识库**，帮助用户理解关系、管理关系、辅助决策。

## 核心原则

- **Decision Support，不是 Decision Maker**：AI 辅助决策，不替用户做决定。
- **事实与推断分离**：每个画像字段都标注 `confirmed / inferred / unknown / conflicting`。
- **未知也是数据**：「婚恋观：未知」是重要的待了解信息，而非空字段。
- **画像持续演化**：Profile v1 → v2 → v3，Skill 版本化。
- **Relationship 是核心实体**，Chat 只是一种数据来源。
- **信息价值随关系阶段变化**：重要的信息，在合适的阶段、用合适的方式了解。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16 · TypeScript · Tailwind CSS v4 · 手写 SVG 雷达图/甘特图 |
| 后端 | Python · FastAPI · SQLAlchemy |
| 数据库 | SQLite（开箱即用）/ PostgreSQL + pgvector（生产） |
| AI | LLM Provider 抽象层（OpenAI/Anthropic/DeepSeek/本地）+ **规则降级**（无 Key 也能跑） |
| Agent | ProfileBuilder / Stage / Score / TurningPoint / Match / Advice / DateReview |

## 快速开始

```powershell
# 一键启动（自动建虚拟环境、装依赖、首次播种演示数据）
.\start.ps1
```

或手动：

```powershell
# 后端（终端 1）
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# 前端（终端 2）
cd frontend
$env:PORT="3000"; npm run dev
```

打开 http://127.0.0.1:3000 。后端 API 文档：http://127.0.0.1:8000/docs 。

## 启用真实 LLM（可选）

默认 `LLM_PROVIDER=none`，系统用规则引擎离线运行。配置后 AI 蒸馏/分析更智能：

```env
# backend/.env
LLM_PROVIDER=deepseek            # 或 openai / anthropic / local
LLM_API_KEY=sk-...
# 本地模型(Ollama)：
# LLM_PROVIDER=local
# LLM_BASE_URL=http://localhost:11434/v1
```

## 项目结构

```
heartmind/
├── frontend/            # Next.js 前端（Dashboard / 甘特图 / 卡片 / 详情抽屉 / 画像Loop / 匹配 / 约会 / 数字人格 / 模拟对话）
├── backend/
│   └── app/
│       ├── models.py            # 18 个数据实体（Relationship 为核心）
│       ├── llm.py               # LLM 抽象层 + 规则降级
│       ├── domain/stages.py     # 关系阶段模型 + 信息价值模型
│       ├── agents/              # 各 Agent + 规则引擎
│       ├── services/            # profile / ingestion / distill / orchestrator
│       └── routers/api.py       # REST API
├── .cursor/skills/              # 三个可复用 Skill
│   ├── wechat-export/           #   导出特定对象微信聊天记录
│   ├── persona-distill/         #   相亲对象画像蒸馏
│   └── self-distill/            #   用户自身画像蒸馏
├── backend/test_flow.py         # 端到端断言测试（9 个核心闭环）
└── backend/seed.py              # 演示数据
```

## 三个 Skill（抽象自开源项目）

- **wechat-export**（源自 `WeChatDataAnalysis`）：按会话 `username` 导出特定对象聊天记录。
- **persona-distill**（改造自 `love-skill`）：将相亲对象蒸馏为 5+1 层 Persona Skill。
- **self-distill**（改造自 `yourself-skill`）：将用户蒸馏为 Self Memory + Persona 双层自我画像。

## 端到端验证

```powershell
cd backend
..\.venv\Scripts\python.exe test_flow.py
```

覆盖：创建对象 → 画像 Loop → 导入聊天 → 时间轴 → 评分 → 匹配 → 约会复盘 → Skill 蒸馏 → 模拟对话 → Dashboard。

## 数据模型（核心）

`User / UserProfile / Person / PersonProfile / Relationship(核心) / RelationshipStage /
Conversation / Message(Conversation Event) / RelationshipEvent / TurningPoint /
DateRecord / ProfileFieldRecord / Memory / RelationshipMetric / CompatibilityMetric /
PersonaSkill / SkillVersion / Advice / Report / AgentRun`

## 路线图（Vertical Slice）

- [x] 第一阶段：创建 Person + Profile Builder Loop + Stage + Information Value
- [x] 第二阶段：导入聊天 → 解析 → Profile/Memory 自动提取
- [x] 第三阶段：Relationship Timeline + State + Turning Point
- [x] 第四阶段：Relationship Score + Compatibility
- [x] 第五阶段：Date Review Loop
- [x] 第六阶段：Persona Skill 蒸馏 + 模拟对话
- [x] 第七阶段：Dashboard + 甘特图 + 关系总览
- [ ] 图片 OCR / 语音 Whisper / 视频 ASR 导入
- [ ] LangGraph 编排更复杂的多 Agent 工作流
- [ ] pgvector 语义检索 + Celery 异步任务
