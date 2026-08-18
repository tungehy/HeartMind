---
name: persona-distill
description: Distill a dating-match partner (相亲对象) into a structured Persona Skill. Use when building or updating a person's profile/persona from chat records, descriptions, or date reviews in HeartMind.
---

# Persona Distill（相亲对象画像蒸馏）

参考 `love-skill-main`，将一位相亲对象蒸馏为结构化 Persona Skill。
遵循 V2 原则：**事实与推断分离、未知也是数据、持续演化（版本化）**。

## 输入

聊天记录 + 人物描述 + Memory + 约会记录 + Timeline + 用户补充。

## 输出：Persona Skill Schema（5+1 层）

```
Layer 0 硬规则（不可违背：基于证据、承认局限、不过度推测）
Layer 1 身份：基本信息 + 性格类型（MBTI/星座/标签）
Layer 2 说话风格：沟通习惯/语言特色/典型对话片段（3-5 段原文）
Layer 3 情感模式：依恋类型/五爱语(1-10)/情绪场景
Layer 4 价值观：优先级/核心价值/生活方式/理想伴侣特征
Layer 5 潜力：优势/挑战/成长性
```

每个字段必须携带：`value / source / confidence / status / evidence / last_updated`。
`status ∈ confirmed | inferred | unknown | conflicting | outdated`。

## 工作流程

1. 收集材料（聊天/描述/约会/记忆）。
2. 逐层填充模板；**无证据的字段标注 `unknown`，不要编造**。
3. 事实（直接提取）与推断（AI 根据行为模式）分开标注。
4. 生成 `Candidate Skill` → 评估 → 落盘为新 `SkillVersion`。
5. 版本递增（v1 → v2 → v3），保留演化历史。

## 蒸馏触发

调用 HeartMind 后端：`POST /api/persons/{id}/skill/distill`。
无 LLM 时由规则引擎产出基础骨架，字段标 `inferred`/`unknown`。

## 参考

- 模板：`love-skill-main/prompts/persona_builder.md`
- 版本管理：`love-skill-main/tools/version_manager.py`
