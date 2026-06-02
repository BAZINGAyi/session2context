# session2context — Agent 集成指南

将 `s2c-data/preferences/` 中的个人偏好接入 AI Agent 的 prompt，使每次对话自动遵守你的工作习惯。

---

## 工作原理

```
session 对话
    ↓  session2context skill 提炼偏好
s2c-data/preferences/      ← 偏好文件（skill 维护内容）
    ↓  skill 读取文件，生成描述，调用脚本刷新下方标记区块
Agent 指令配置文件              ← 告诉 agent 读哪些文件、读什么
    ↓  每次对话开始时
LLM 上下文                     ← 自动注入偏好，无需重复交代
```

`<!-- s2c:start -->` 到 `<!-- s2c:end -->` 之间的区块由 skill 的脚本自动维护，**请勿手动编辑**。每次偏好更新后，skill 会重新读取各文件内容，刷新描述。

> **注入是互斥的**：skill 只会注入**一处**，按以下优先级取第一个**已包含标记区块**的文件：
> 1. `.cursor/rules/session2context.mdc`
> 2. 项目根目录 `CLAUDE.md`
> 3. 项目根目录 `AGENTS.md`
>
> 因此你**只需为常用的那个平台**配置一个带标记的文件即可。

---

## 各平台集成（任选其一）

### Cursor

新建文件 `.cursor/rules/session2context.mdc`（文件名固定，skill 据此查找），内容如下：

```markdown
---
description: 用户个人偏好与工作习惯
alwaysApply: true
---

用户有一套个人偏好，在每次对话开始时，读取以下文件的完整内容，并在整个对话中遵守：

<!-- s2c:start -->
<!-- s2c:end -->

如果文件内容为空或仅有注释，则忽略，不影响正常对话。
```

---

### Claude Code

在项目根目录的 `CLAUDE.md` 中追加以下内容：

```markdown
## 用户偏好

在每次对话开始时，读取以下文件的完整内容并遵守：

<!-- s2c:start -->
<!-- s2c:end -->

如果文件内容为空或仅有注释，则忽略。
```

---

### OpenCode / 其他 Agent（AGENTS.md）

在项目根目录的 `AGENTS.md` 中追加以下内容：

```markdown
## 用户偏好

在每次对话开始时，读取以下文件的完整内容并遵守：

<!-- s2c:start -->
<!-- s2c:end -->

如果文件内容为空或仅有注释，则忽略。
```

---

## 首次使用

1. 按上方模板，为你常用的平台创建**一个**带标记区块的指令配置文件
2. 在对话中显式点名触发（说 "session2context" 或 "运行 session2context"）
3. skill 完成提炼后，会自动读取 `preferences/` 各文件内容，生成描述，调用脚本填入 `<!-- s2c:start/end -->` 区块

> 脚本只负责在已存在的标记区块内注入，**不会自动创建文件**。若 skill 提示"未找到注入目标"，说明你还没按第 1 步创建带标记的文件。

## 示例

首次注入后的效果示例：

```markdown
<!-- s2c:start -->
- `s2c-data/preferences/profile.md` — 涵盖：沟通、协作流程、偏好与禁忌。所有对话必读。
- `s2c-data/preferences/proj-overview.md` — 涵盖：技术栈、命令、结构与约定。涉及本项目操作时必读。
<!-- s2c:end -->
```
