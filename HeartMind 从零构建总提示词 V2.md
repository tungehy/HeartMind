# HeartMind 从零构建总提示词 V2

你现在需要从零设计并逐步实现一个名为 **HeartMind** 的 AI 关系智能平台。

HeartMind 的核心定位不是普通的“恋爱聊天机器人”，而是：

> **一个以项目管理思想管理相亲交往全生命周期的 AI Relationship Intelligence Platform。**

核心理念：

> **Relationship as Project**

用户与每一个相亲对象之间的关系，都被视为一个独立的长期项目（Relationship Project）。

聊天、见面、约会、礼物、冲突、关系升温、关系降温、重新联系等，都属于这个项目中的不同事件。

HeartMind 使用 AI Agent 将碎片化聊天、约会记录、人物信息和历史行为整合起来，形成一份不断更新的“关系知识库”，帮助用户理解关系、管理关系，并在沟通和决策过程中提供辅助。

注意：

**AI 不能声称知道另一个人的真实想法。**

所有“兴趣”“情绪”“关系趋势”“匹配程度”等结论都必须明确区分：

- 用户明确提供的信息
- 聊天中直接提取的信息
- 约会中直接获得的信息
- AI 根据行为模式推断的信息
- 当前无法确认的信息

对于不确定内容必须支持：

- 未知
- 未提及
- 待确认
- AI 推测

不能把 AI 推测当作事实。

---

# 一、核心产品理念

HeartMind 不应该围绕“聊天”设计，而应该围绕：

```text
人物
 ↓
关系
 ↓
事件
 ↓
状态
 ↓
分析
 ↓
决策
```

展开。

一个完整的 Relationship Project：

```text
认识
 ↓
建立联系
 ↓
持续聊天
 ↓
第一次见面
 ↓
关系升温 / 平稳 / 降温
 ↓
多次约会
 ↓
暧昧
 ↓
稳定关系
 ↓
继续发展
 或
关系结束
```

真实关系不是严格线性的，因此状态允许反复变化：

```text
升温 → 降温 → 升温
稳定 → 降温 → 重新联系
见面 → 冷却 → 再次约会
```

所以系统应该采用：

> **Timeline + Event + Relationship State**

而不是简单的线性状态机。

---

# 二、最重要的核心功能：Profile Builder Loop

HeartMind 最核心、最有特色的交互，不是普通表单，而是类似 Cursor Plan Mode 的：

> **画像构建循环（Profile Builder Loop）**

用户创建新的相亲对象时，不应该要求用户一次性填写几十个字段。

应该允许用户只提供：

```text
“这是我最近认识的一个女生，她27岁，在南通工作，喜欢旅游，好像是老师。”
```

或者：

```text
导入微信聊天记录。
```

或者：

```text
输入一段人物介绍。
```

系统首先建立一个初步画像。

然后启动：

# 画像构建循环

```text
用户提供资料
        ↓
Profile Analyzer
        ↓
提取已知信息
        ↓
识别未知信息
        ↓
判断当前关系阶段
        ↓
评估哪些信息“当前值得了解”
        ↓
生成下一轮问题 / 选项
        ↓
用户回答
        ↓
更新 Profile
        ↓
更新 Memory
        ↓
更新 Relationship Context
        ↓
重新评估关系阶段与信息价值
        ↓
判断是否继续循环
```

这里有一个非常重要的原则：

> **Profile Builder 的目标不是尽快把所有字段填满，而是在当前关系阶段，以自然、合理的方式逐渐建立足够准确的人物画像。**

---

# 三、Relationship Stage：画像构建必须理解恋爱阶段

HeartMind 必须建立：

> **Relationship Stage Model**

因为“应该了解什么”与“什么时候了解”高度相关。

建议初始阶段：

```text
STAGE_0
尚未认识

STAGE_1
刚认识

STAGE_2
初步了解

STAGE_3
持续互动

STAGE_4
关系升温

STAGE_5
暧昧 / 互有好感

STAGE_6
稳定交往

STAGE_7
深入了解 / 长期规划

STAGE_8
关系降温

STAGE_9
关系结束
```

实际开发时不要强制要求所有关系严格经过这些阶段。

例如：

```text
刚认识 → 降温 → 结束

刚认识 → 持续互动 → 降温 → 重新升温

持续互动 → 第一次见面 → 继续互动

暧昧 → 稳定交往
```

都应该允许。

---

# 四、Information Value / 信息价值模型

这是 HeartMind 非常重要的核心机制。

系统不能简单地：

> 缺什么字段 → 就问什么。

而应该判断：

> **这个信息当前是否值得了解？**

因此每一个未知信息都应该计算：

```text
Information Value
```

但 Information Value 不是固定数值，而应该是：

> **Context-aware Information Value**

即：

> **与当前关系阶段相关的信息价值。**

---

# 五、Information Value 的核心组成

一个信息当前是否值得了解，可以综合：

```text
Relationship Stage
+
Compatibility Impact
+
Conversation Naturalness
+
Sensitivity
+
Urgency
+
Current Evidence
+
User Goal
+
Potential Decision Impact
```

例如：

### 刚认识

可能高价值：

```text
兴趣爱好

生活方式

工作大致情况

周末活动

聊天偏好

基础性格

```

可能低价值：

```text
收入

资产

家庭矛盾

生育计划

非常具体的婚姻安排
```

不是说这些信息不重要。

而是：

> **现在可能不是合适的了解时机。**

---

# 六、信息应该拥有“时机”

每一个 Profile Field 不仅有：

```text
value
```

还应该有：

```text
timing
```

例如：

```json
{
  "field": "marriage_view",
  "value": null,
  "status": "unknown",
  "timing": "later",
  "information_value": 0.82
}
```

其中：

```text
now
soon
later
not_relevant
unknown
```

例如：

```text
婚恋观：

重要程度：★★★★★

当前了解价值：★★☆☆☆

原因：

关系阶段较早，直接询问可能过于突兀。

建议：

在关系进一步升温后，通过自然聊天逐渐了解。
```

这比单纯的“未知字段”更加符合真实相亲场景。

---

# 七、Information Value 必须动态变化

例如：

第一次见面：

```text
未来城市规划

Information Value：0.35
```

关系升温以后：

```text
Information Value：0.78
```

进入长期交往：

```text
Information Value：0.95
```

因此：

> **信息价值不是 Profile 的静态属性，而是 Relationship Context 的动态函数。**

---

# 八、信息获取方式也需要由 AI 判断

不是所有信息都应该通过直接提问获取。

系统应该判断：

```text
直接询问

自然聊天

观察行为

约会观察

用户补充

等待未来事件

AI从聊天中推断

暂时未知
```

例如：

“喜欢什么音乐？”

可以直接问。

但：

“消费观如何？”

更适合通过：

```text
聊天

约会

消费行为

生活方式
```

逐渐形成判断。

所以系统输出应该类似：

> 当前不建议直接询问，可以通过下一次约会中的消费选择和生活方式自然观察。

---

# 九、用户可以选择“不知道”

这是必须支持的核心交互。

每个待确认信息都允许：

```text
知道

不知道

暂时不想了解

之后从聊天中自动推断

以后再说

跳过
```

例如：

```text
她的生日？

[ 已知：7月18日 ]

[ 不知道 ]

[ 以后再了解 ]
```

用户选择“不知道”以后：

不要无限追问。

记录：

```text
birthday
value = null
status = unknown
source = user
```

系统之后等待新的聊天或约会信息自动补充。

---

# 十、画像必须有 Confidence

所有画像字段都应该包含：

```text
value
source
confidence
last_updated
evidence
status
timing
```

例如：

```json
{
  "field": "height",
  "value": 168,
  "source": "conversation",
  "confidence": 0.96,
  "status": "confirmed",
  "evidence": "我身高168",
  "last_updated": "2026-08-10",
  "timing": "known"
}
```

另外：

```text
confirmed
inferred
unknown
conflicting
outdated
```

必须区分。

如果不同聊天中出现冲突：

```text
聊天 A：168

聊天 B：170
```

不能静默覆盖。

应该标记：

```text
信息冲突
```

并交由用户确认或由后续 Agent 处理。

---

# 十一、画像收敛机制

每一次 Profile Builder Loop 结束后，需要给用户一个“小结”。

例如：

## 当前画像

已经确认：

- 27岁
- 教师
- 南通
- 喜欢旅游
- 喜欢猫
- 周末经常运动

初步推断：

- 性格偏慢热
- 分享欲中等偏高
- 对熟悉话题回复较积极

尚未了解：

- 婚恋观
- 未来城市规划
- 家庭情况
- 消费观

其中：

```text
婚恋观
重要程度：高
当前阶段：暂缓
```

而：

```text
兴趣爱好
重要程度：中
当前阶段：适合了解
```

当前画像完整度：

**68%**

当前阶段最值得继续了解：

> 未来生活方式、兴趣偏好

建议暂缓：

> 婚姻、生育、家庭资产等高敏感信息

然后询问：

```text
是否继续完善画像？

[继续]

[暂时结束]
```

用户选择“暂时结束”以后，本轮 Loop 结束。

---

# 十二、用户自己的 Profile 也使用同一套机制

HeartMind 不仅要分析相亲对象。

还必须逐渐建立：

> **User Profile / 用户画像**

因为真正有价值的匹配分析必须是：

```text
相亲对象 Profile
        ×
用户 Profile
        ↓
Compatibility Analysis
```

用户第一次进入 HeartMind 时，不需要填写大量表单。

也采用同样的：

> Profile Builder Loop

例如系统问：

```text
你对未来伴侣最看重什么？
```

可以直接回答，也可以选择：

```text
稳定

性格

外貌

价值观

家庭

事业

不知道
```

然后继续构建：

```text
个人基础信息

生活习惯

兴趣

消费观

婚恋观

家庭观

事业规划

城市偏好

择偶偏好

底线

加分项

沟通方式

情绪模式

社交方式

关系期待
```

---

# 十三、用户 Profile 也必须动态更新

用户画像不能是静态问卷。

例如最初：

```text
未来城市：未知
```

后来用户在聊天复盘中多次表达：

```text
希望未来在江苏发展
```

系统可以建议：

> 发现你的长期城市偏好可能发生变化，是否更新用户画像？

```text
[更新]

[保持原设置]
```

从而建立：

> **User Digital Twin**

---

# 十四、使用 awesome-persona-skills 作为 Persona Skill 基础

参考：

https://github.com/tmstack/awesome-persona-skills

可以将其作为 HeartMind Persona Skill 层的参考基础和初始模板。

不要简单复制整个仓库。

HeartMind 应建立自己的：

```text
Persona Skill Schema
```

一个对象 Skill 至少包含：

```text
身份概述

基本信息

性格特征

沟通风格

语言习惯

兴趣偏好

价值观

关系观

情绪模式

聊天节奏

主动程度

敏感话题

雷区

喜欢的话题

不喜欢的话题

典型回复风格

常用表达

重要记忆

关系历史

对用户的互动模式

当前关系状态

不确定信息
```

---

# 十五、Persona Skill Distillation

对象 Skill 不应该一开始生成完整版本。

应该随着信息增加逐渐蒸馏。

过程：

```text
聊天记录
+
人物资料
+
Memory
+
约会记录
+
Relationship Timeline
+
用户补充
        ↓
Skill Distillation Agent
        ↓
Candidate Skill
        ↓
Skill Evaluator
        ↓
最终 Persona Skill
```

Skill 需要记录：

```text
version

created_at

updated_at

evidence

confidence
```

实现：

```text
林小雨.skill v1
林小雨.skill v2
林小雨.skill v3
```

这样可以看到：

> AI 对这个人的理解是如何逐渐演化的。

---

# 十六、聊天数据层

系统应该支持多种数据输入。

优先支持：

```text
微信聊天记录

手动输入

文本导入

Markdown

JSON

CSV
```

后续支持：

```text
图片

语音

视频

文件
```

对于：

```text
图片 → OCR

语音 → Whisper

视频 → ASR + 内容分析
```

最终统一转换成：

```text
Conversation Event
```

---

# 十七、Conversation Event Schema

每条聊天消息应尽量保留：

```text
relationship_id

sender

receiver

timestamp

message_type

content

media_reference

reply_to

source
```

同时生成：

```text
semantic_embedding

topics

emotion

intent

entities

importance
```

不要在数据库里只保存：

```text
content
```

后续 AI 分析需要结构化信息。

---

# 十八、Relationship Timeline

所有关系都建立 Timeline。

Timeline Event 示例：

```text
开始认识

第一次聊天

关系升温

关系稳定

关系降温

第一次见面

第二次见面

送礼

重要话题

冲突

冷战

重新联系

关系结束
```

每一个 Timeline Event 都应该包含：

```text
时间

事件类型

事件摘要

关系阶段

关系评分变化

AI分析

证据

可信度
```

---

# 十九、Turning Point

聊天分析板块的重点：

> **关系转折点**

AI 自动识别。

例如：

```text
7月18日

聊天内容发生变化

↓

7月19日至22日

平均回复间隔增加

↓

主动开启话题次数下降

↓

AI：

检测到一次明显的关系降温节点
```

Timeline 标记：

```text
⚠ 关系转折点
```

点击以后展示：

```text
发生了什么

为什么认为它是转折点

支持证据

变化前

变化后

可能原因

建议
```

必须强调：

AI 输出是：

> “基于聊天行为的推断”

而不是：

> “她就是因为某件事情不喜欢你”。

---

# 二十、Relationship Score

建立综合关系评分。

但不要使用一个简单的黑盒数字。

应该拆成：

```text
关系综合评分

沟通质量

互动积极度

兴趣匹配

价值观匹配

情绪连接

见面表现

主动程度

稳定性

未来规划匹配

用户主观满意度
```

同时显示：

```text
当前评分

评分变化

评分趋势

主要加分因素

主要扣分因素

数据完整度

判断可信度
```

---

# 二十一、Compatibility Analysis

核心输入：

```text
User Profile

+

Person Profile

+

Relationship History
```

输出：

```text
总体匹配程度

价值观匹配

生活方式匹配

兴趣匹配

城市规划匹配

婚恋观匹配

沟通方式匹配

家庭观念匹配

未来规划匹配
```

同时区分：

```text
已确认匹配

未知

存在冲突

AI推测
```

不要为了生成一个数字而强行评分。

最重要的是：

> **告诉用户“不知道什么”。**

例如：

```text
当前匹配度：较高

判断可信度：中等

主要原因：

双方未来城市规划尚未明确。

建议优先了解：

未来几年更希望在哪个城市发展？
```

但如果当前关系阶段较早，则不应该直接建议询问。

应该输出：

> 当前暂不建议直接讨论长期城市规划，可以先从工作规划、城市生活体验等低压力话题逐步了解。

---

# 二十二、聊天建议

聊天建议必须基于：

```text
用户 Profile
+
对象 Profile
+
关系阶段
+
缺失信息
+
最近聊天
+
Timeline
+
Relationship State
```

例如：

对象未来城市规划 = 未知

用户明确希望长期留在南通。

系统可以建议：

> 当前不建议直接询问“你以后愿不愿意来南通”，可以先自然聊工作规划、城市生活和未来安排。

重点不是给用户一句机械话术，而是：

> **告诉用户为什么聊、应该从什么方向聊、现在是否适合聊。**

---

# 二十三、约会复盘也采用 Profile Builder Loop

约会复盘不能只是：

```text
填写表单
→
AI总结
```

而应该成为第二个重要的：

> **Relationship Review Loop**

用户约会结束后，首先只需要自然描述：

```text
今天和她吃了火锅，聊了工作、大学和旅游。
她说最近工作有点忙，但周末喜欢出去玩。
整体感觉比较轻松，后来一起散了会儿步。
我觉得她今天比聊天时更活泼。
```

用户不需要填写大量结构化字段。

---

# 二十四、第一轮 AI 分析

AI 首先提取：

```text
约会时间

地点

持续时间

聊天主题

重要事件

对方表现

用户表现

用户主观感受

关系变化

新增人物信息

潜在冲突

潜在升温点
```

然后更新：

```text
Profile

Memory

Timeline

Relationship State
```

---

# 二十五、第二轮：约会复盘问题生成

AI 根据第一轮描述：

```text
当前 Profile
+
历史聊天
+
历史约会
+
Relationship Stage
+
本次约会内容
```

识别：

> **哪些信息仍然不确定，并且值得通过用户回忆本次约会进一步补充。**

然后生成下一轮问题。

例如：

```text
我已经基本了解这次约会的整体情况。

还有三个信息可能影响后续判断：

① 她主动提到了几次未来规划？
② 你们讨论工作时，她的情绪是积极还是偏压力？
③ 你感觉这次见面后，她对你的主动程度有没有变化？
```

用户可以：

```text
回答

不知道

记不清

跳过
```

---

# 二十六、约会复盘也允许多轮 Loop

完整流程：

```text
用户自然描述约会
        ↓
Date Review Agent
        ↓
提取事件
        ↓
更新临时约会记录
        ↓
识别信息缺口
        ↓
结合 Relationship Stage
        ↓
计算 Information Value
        ↓
生成下一轮问题
        ↓
用户回答
        ↓
更新 Date Record
        ↓
更新 Profile
        ↓
更新 Memory
        ↓
更新 Relationship
        ↓
判断是否收敛
```

当信息足够时：

```text
本次约会复盘已完成
```

然后输出：

## 约会复盘总结

```text
本次约会评价：较好

关系变化：轻微升温

主要原因：

+ 主动分享个人经历
+ 主动提出下次活动

需要关注：

- 对未来规划仍缺乏信息

新增人物信息：

- 喜欢周末短途旅行
- 工作压力较大

建议：

下次可以继续围绕兴趣和生活方式展开。
```

---

# 二十七、约会复盘必须考虑“当时看不到的信息”

约会结束时，有些东西本来就无法判断。

不要强迫 AI 给结论。

例如：

```text
她是否真的对你有长期兴趣？
```

如果证据不足：

```text
当前无法判断
```

并记录：

```text
future_information_target
```

例如：

> 后续观察她是否会主动提出下一次见面。

这会成为未来 Timeline 的观察指标。

---

# 二十八、约会内容也必须进入知识库

例如：

用户描述：

> 她说毕业后想去杭州发展，喜欢周末去咖啡店看书，父母目前住在南通。

系统自动提取：

```text
未来城市 = 杭州

兴趣 = 咖啡 / 阅读

家庭所在地 = 南通
```

然后：

```text
更新 Profile

更新 Memory

更新 Compatibility

更新 Relationship Timeline
```

同时记录：

```text
source = date_review
```

---

# 二十九、多 Agent 架构

不要设计成一个“大 Agent”。

建议：

```text
                    HeartMind
                        │
             Relationship Orchestrator
                        │
       ┌────────────────┼────────────────┐
       │                │                │
 Profile Agent     Chat Agent      Timeline Agent
       │                │                │
 Memory Agent      Turning Agent   Score Agent
       │                │                │
 Skill Agent       Advice Agent    Match Agent
       │                │                │
 Date Review Agent  Stage Agent    Simulation Agent
       └───────────────┼────────────────┘
                       │
              Relationship Knowledge
                       │
               User / Person / Event
```

---

# 三十、Stage Agent

新增一个核心 Agent：

> **Relationship Stage Agent**

负责判断：

```text
当前处于什么关系阶段

是否发生阶段变化

是否出现升温

是否出现降温

是否进入新的关系阶段

判断依据是什么
```

例如：

```text
当前阶段：

持续互动 → 关系升温

置信度：0.81
```

证据：

```text
主动聊天次数增加
回复速度提升
开始分享个人经历
主动提出见面
```

---

# 三十一、Profile Builder Agent

这是 HeartMind 最核心的 Agent。

它不是普通聊天 Agent。

它有自己的 Loop：

```text
读取当前 Profile

↓

读取已有证据

↓

读取当前 Relationship Stage

↓

识别未知字段

↓

计算 Context-aware Information Value

↓

过滤当前不适合了解的信息

↓

选择下一步最值得了解的问题

↓

等待用户输入

↓

解析用户回答

↓

更新 Profile

↓

更新 Memory

↓

重新计算完整度

↓

判断是否收敛
```

系统状态：

```text
collecting

clarifying

converging

paused

completed
```

---

# 三十二、Profile Builder 的停止条件

当：

```text
核心字段完整度较高

+

高价值未知信息减少

+

当前阶段适合了解的信息已经基本覆盖

+

继续询问的边际收益降低
```

则自动进入：

```text
converged
```

然后输出总结。

注意：

> **Profile Complete ≠ 所有字段都已知。**

真正的完成意味着：

> **在当前关系阶段，已经没有必要继续主动追问。**

---

# 三十三、模拟对话

用户完成一定程度的 Profile + Skill 蒸馏后：

进入：

> 模拟对话

调用：

```text
Person Skill

+

最新 Memory

+

Relationship Context

+

最近聊天记录
```

模拟对象。

支持：

```text
真实聊天模式

训练模式

压力测试模式

约会前演练
```

训练模式可以指出：

```text
这里的问题：

你连续追问了三个问题。

建议：

先回应她当前表达，再继续问。
```

---

# 三十四、Relationship Knowledge Base

每位对象自动生成一份不断演化的关系知识库。

例如：

```text
林小雨

========

【基础资料】

【家庭】

【职业】

【兴趣】

【价值观】

【约会记录】

【重要事件】

【聊天禁区】

【送礼记录】

【长期目标】

【AI建议】

【关系演化】

【时间轴】

【未知信息】

【待观察信息】
```

以后用户不需要翻大量聊天记录。

只需要查看：

> **这份不断更新的“关系档案”。**

---

# 三十五、Relationship Replay

像 Git 提交历史一样回放一段关系。

例如：

```text
2026-03-12
第一次聊天

↓

2026-03-18
第一次见面

↓

2026-03-25
连续每天聊天

↓

2026-04-02
讨论收入
⚠ 转折点

↓

2026-04-10
回复速度明显下降

↓

2026-04-18
AI判断进入“关系降温”

↓

2026-04-28
恢复联系

↓

2026-05-03
第二次见面
```

每一个节点都能展开：

- 当时发生了什么
- 当时的聊天摘要
- AI 对关系变化的分析
- 当时可观察到的证据
- 当时的信息是否充分
- AI 当时可能给出的建议
- 最终结果

---

# 三十六、Dashboard

首页采用专业 AI SaaS Dashboard。

顶部：

> **关系总览**

核心区域：

## 关系甘特图

展示所有相亲对象：

```text
林小雨 ━━━━━━━━━━━━━━━

陈思思 ━━━━━━━

李梦琪 ━━━━━━━━━

王梓涵 ━━━
```

颜色：

```text
开始

升温

平稳

降温

见面

冲突

结束
```

关键节点：

```text
⚠ 转折点

❤️ 见面

🔥 升温
```

---

# 三十七、对象卡片

按照：

> Relationship Score

从高到低排列。

每张卡：

```text
头像

姓名

年龄

城市

综合评分

评分趋势

关系状态

关系雷达图

兴趣标签

画像完整度

最近记忆

最近聊天

AI建议
```

---

# 三十八、对象详情页

建议：

```text
概览

聊天分析

关系时间轴

人物画像

长期记忆

关系评分

匹配分析

约会记录

Digital Twin

模拟对话

AI建议
```

---

# 三十九、聊天分析页

重点：

```text
聊天时间线

关系趋势

情绪趋势

主动程度

聊天主题

关键事件

Turning Points

踩雷点

升温点

AI分析
```

例如：

```text
7月12日
↑ 关系升温

7月19日
⚠ 关系转折

7月22日
↓ 关系降温

7月28日
↑ 重新升温
```

点击节点查看证据。

---

# 四十、匹配分析页

展示：

```text
用户画像

        ×

对象画像
```

形成：

```text
匹配雷达

匹配优点

潜在冲突

未知区域

需要进一步了解的问题
```

其中：

> **未知区域**

应该成为非常重要的 UI。

例如：

```text
婚恋观：未知

未来城市：未知

生育计划：未知

消费观：部分未知
```

然后系统结合当前 Relationship Stage 给出建议：

```text
现在适合了解

近期适合了解

暂时不要主动询问

适合通过约会观察
```

---

# 四十一、AI 建议系统

AI 建议不应该只是：

> “你应该怎么做”。

而应该拆成：

```text
当前状态

发现

证据

风险

机会

建议

建议时机

建议方式
```

例如：

```text
当前：

持续互动阶段

发现：

对方最近开始主动分享生活。

证据：

过去7天主动开启话题增加40%。

建议：

可以适当增加线下互动。

时机：

未来一周。

方式：

从共同兴趣切入，而不是直接谈关系。
```

---

# 四十二、Relationship Score

建立综合关系评分。

拆成：

```text
沟通质量

互动积极度

兴趣匹配

价值观匹配

情绪连接

见面表现

主动程度

稳定性

未来规划匹配

用户主观满意度
```

同时显示：

```text
当前评分

评分变化

评分趋势

主要加分因素

主要扣分因素

数据完整度

判断可信度
```

---

# 四十三、数据模型

至少设计：

```text
User

Person

Relationship

Conversation

Message

ConversationSession

RelationshipEvent

TurningPoint

DateRecord

ProfileField

Memory

RelationshipMetric

CompatibilityMetric

PersonaSkill

SkillVersion

Advice

Report

AgentRun

RelationshipStage
```

其中：

```text
Relationship
```

是整个系统最核心的实体。

---

# 四十四、ProfileField 数据模型

建议 ProfileField 至少包含：

```text
id

person_id

field_name

value

value_type

source

evidence

confidence

status

timing

information_value

sensitivity

last_updated

valid_from

valid_until
```

这样未来才能实现：

```text
信息演化

信息冲突

信息过期

信息来源追踪

阶段性信息价值
```

---

# 四十五、Agent 输出必须可追溯

所有重要 AI 结论必须记录：

```text
agent

model

prompt_version

input_reference

output

confidence

created_at
```

例如：

```text
Relationship Score = 82

来源：

Relationship Agent v2

依据：

过去14天聊天

2次约会

18条Memory
```

这样系统未来才能：

```text
重新分析

比较模型

审计错误

优化Prompt

回放Agent决策
```

---

# 四十六、技术架构

前端：

```text
React / Next.js

TypeScript

Tailwind CSS

shadcn/ui

Recharts

React Flow
```

后端：

```text
Python

FastAPI

SQLAlchemy

PostgreSQL
```

AI：

```text
LLM Provider abstraction

支持 OpenAI / Anthropic / DeepSeek / 本地模型
```

Agent：

```text
LangGraph
```

Embedding：

```text
pgvector
```

异步任务：

```text
Celery / Redis
```

文件：

```text
本地对象存储 / S3兼容存储
```

---

# 四十七、Repository 结构建议

```text
heartmind/
│
├── frontend/
│
├── backend/
│
├── agents/
│
├── skills/
│
│   ├── personas/
│   │   ├── person/
│   │   └── user/
│   │
│   ├── relationship/
│   ├── conversation/
│   ├── date_review/
│   └── simulation/
│
├── prompts/
│
├── models/
│
├── services/
│
├── ingestion/
│
│   ├── wechat/
│   ├── text/
│   ├── audio/
│   └── image/
│
├── tests/
│
└── docs/
```

---

# 四十八、开发方式

不要一次性生成所有功能。

采用：

> **Vertical Slice Development**

每完成一个核心闭环再继续。

---

## 第一阶段

```text
创建 Person

↓

Profile Builder Loop

↓

Profile 保存

↓

Profile 总结
```

同时实现：

```text
Relationship Stage

Information Value

Unknown / Later / Confirmed
```

---

## 第二阶段

```text
导入聊天

↓

消息解析

↓

Profile 自动提取

↓

Memory 自动提取
```

---

## 第三阶段

```text
Relationship Timeline

↓

Relationship State

↓

Turning Point
```

---

## 第四阶段

```text
Relationship Score

↓

Compatibility
```

---

## 第五阶段

```text
创建 Date Record

↓

自然描述约会

↓

Date Review Loop

↓

AI生成下一轮问题

↓

用户补充

↓

Profile / Memory / Relationship 更新
```

---

## 第六阶段

```text
Persona Skill

↓

Skill Distillation

↓

模拟对话
```

---

## 第七阶段

```text
Dashboard

↓

甘特图

↓

关系总览
```

---

# 四十九、第一版 MVP

第一版优先实现：

```text
1. 用户画像

2. 相亲对象画像

3. Profile Builder Loop

4. Relationship Stage

5. Context-aware Information Value

6. 微信聊天导入接口

7. 聊天内容解析

8. 基础 Profile 抽取

9. Memory 抽取

10. Relationship Timeline

11. Relationship State

12. Relationship Score

13. Date Review Loop

14. Persona Skill

15. 模拟对话

16. Dashboard
```

暂缓：

```text
复杂社交网络

高级预测

自动发消息

复杂推荐算法

多渠道自动化
```

---

# 五十、最重要的产品原则

## 原则一

**不要让 AI 替用户做决定。**

HeartMind 是：

```text
Decision Support
```

而不是：

```text
Decision Maker
```

---

## 原则二

**事实与推断必须分离。**

例如：

```text
事实：

她说自己喜欢旅游。

推断：

她可能比较重视生活体验。
```

二者必须在数据结构和 UI 上有所区别。

---

## 原则三

**未知也是数据。**

例如：

```text
婚恋观：

未知
```

这不是空字段。

而是：

> 当前关系中非常重要的未知信息。

---

## 原则四

**画像不是一次生成，而是持续演化。**

```text
Profile v1
↓
Profile v2
↓
Profile v3
```

---

## 原则五

**Relationship 是核心实体，Chat 只是 Relationship 的一种数据来源。**

---

## 原则六

**所有 AI 结论都必须可以追溯到证据。**

---

## 原则七

**信息价值必须考虑关系阶段。**

不是：

> 重要的信息就马上问。

而是：

> **重要的信息，在合适的关系阶段，通过合适的方式了解。**

---

## 原则八

**Profile Builder 的目标不是填满表格，而是逐渐降低关系认知的不确定性。**

---

# 五十一、最终产品体验

理想状态下，新用户第一次打开 HeartMind，不是：

```text
请填写：

姓名：

年龄：

身高：

学历：

职业：

……
```

而是：

```text
欢迎使用 HeartMind

先告诉我一些关于这个人的信息。

你可以直接描述她，
也可以导入你们的聊天记录。

例如：

“她叫小雨，27岁，在南通当老师，
喜欢旅游和猫，性格比较慢热。”
```

用户输入以后：

```text
AI：

我已经建立了初步画像。

目前已经确认 7 项信息。

还有 5 项信息值得后续了解。

不过考虑到你们目前只是刚认识，
我建议暂时不要主动了解其中的3项。

当前最值得了解的是：

① 她平时的兴趣和周末生活
② 她对工作和城市生活的感受

你可以：

[继续完善]

[暂时结束]

[查看当前画像]
```

用户进入：

```text
画像详情
```

之后整个 HeartMind 的其他模块都开始围绕这份不断成长的画像运行。

约会结束后也不是填写复杂问卷，而是：

```text
今天怎么样？

你可以直接告诉我发生了什么。
```

用户自然描述以后：

```text
AI：

我已经记录了这次约会。

目前有几个信息值得进一步确认：

① 她提到未来工作规划时是什么态度？
② 你感觉她主动提出下一次见面的意愿如何？

也可以选择：

[不知道]

[记不清]

[暂时跳过]
```

最终形成：

```text
                    HeartMind
                        │
                 ┌──────┴──────┐
                 │             │
             用户画像       对象画像
                 │             │
                 └──────┬──────┘
                        │
                Relationship
                        │
        ┌───────────────┼───────────────┐
        │               │               │
      Chat            Date           Timeline
        │               │               │
        └───────────────┼───────────────┘
                        │
                 Knowledge Base
                        │
              ┌─────────┼─────────┐
              │         │         │
            Match      Advice    Skill
              │         │         │
              └─────────┼─────────┘
                        │
                   AI Assistant
```

**最终目标：**

让 HeartMind 从“帮你分析聊天记录”，逐步进化成：

> **一个持续理解你、理解对方、理解这段关系，并随着关系发展不断更新自己的 AI Relationship Manager。**

它不会要求用户一次性把一个人“了解清楚”，而是像一个真正的关系管理助手一样，知道**现在知道什么、还不知道什么、什么值得了解、什么时候适合了解，以及应该通过什么方式自然地了解**。

这也是 HeartMind 与普通“聊天分析 AI”最大的区别。