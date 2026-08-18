---
name: self-distill
description: Distill the user themself into a structured Self Persona Skill (User Digital Twin). Use when building or updating the user's own profile (values, preferences, communication style, boundaries, mate criteria) in HeartMind.
---

# Self Distill（自身画像蒸馏 / User Digital Twin）

参考 `yourself-skill-master`，将用户自己蒸馏为 Self Skill。
真正有价值的匹配 = 对象画像 × 用户画像（V2 第十二节）。

## 输入

结构化问答 + 聊天/日记/社媒 + 口述。采用与对象画像相同的 Profile Builder Loop。

## 输出：双层结构

```
Part A — Self Memory（事实性自我认知）
  核心身份 / 核心价值观(工作观·金钱观·人际观·成长观·核心矛盾)
  生活习惯 / 重要记忆 / 人际关系图谱 / 成长轨迹

Part B — Persona（行为规则，分层）
  Layer 0 硬规则（保留棱角、不人生导师化）
  Layer 1 身份 / Layer 2 说话风格 / Layer 3 情感与决策(含自我对话)
  Layer 4 人际行为 / Layer 5 边界与雷区
```

## 用户画像需覆盖的维度（V2 第十二节）

个人基础信息 / 生活习惯 / 兴趣 / 消费观 / 婚恋观 / 家庭观 / 事业规划 /
城市偏好 / 择偶偏好 / 底线 / 加分项 / 沟通方式 / 情绪模式 / 社交方式 / 关系期待。

## 关键机制

- **动态更新**：发现用户偏好变化时，提示「是否更新画像」（[更新]/[保持原设置]）。
- **Correction**：用户纠正时记录 Correction 并修订，不静默覆盖。
- **允许"不知道"**：每个待确认项支持 知道/不知道/以后再说/跳过。

## 蒸馏触发

调用 HeartMind 后端：`POST /api/user/skill/distill`。

## 参考

- 模板：`yourself-skill-master/prompts/self_builder.md`、`persona_builder.md`
- 运行规则：`yourself-skill-master/tools/skill_writer.py`
