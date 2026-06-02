# session2context

> 从对话中提炼个人习惯，让 AI Agent 在每次对话中自动记住你的工作方式。

---

## 它解决什么问题

AI 对话是无状态的。每次新会话，agent 对你一无所知——不知道你偏好中文回复，不知道你要先看方案再确认，
不知道这个项目的技术约定。你只能反复交代，或者维护一份越写越长、却越来越难跟上实际习惯的系统提示。

`session2context` 换了一种思路：
**不让你手写说明书，而是从真实的工作对话中提取习惯信号**。每次 session 结束后，它将观察到的行为模式提炼成结构化偏好，
自动注入后续每次对话的上下文。随着会话积累，agent 对你的了解越来越准，协作越来越默契。

---

## 工作流

```
当前对话
  ↓  说"session2context"触发 skill
s2c-data/sessions/      ← 原始摘要（用户确认后写入）
  ↓  用户确认后提炼
s2c-data/preferences/   ← 持久化偏好（profile.md / proj-overview.md）
  ↓  提炼写入后，skill 刷新描述
Agent 指令配置文件        ← 告诉 Agent 每次读哪些偏好文件
  ↓  每次新对话开始
LLM 上下文              ← 偏好自动注入，无需重复交代
```

---

## 前置要求

- Python 3（用于运行 `scripts/refresh_markers.py`）
- 项目根目录读写权限

---

## 安装

**方式一：手动复制**

将 `session2context/` 文件夹复制到你项目的 `skills/` 目录下：

```
your-project/
└── skills/
    └── session2context/
        ├── SKILL.md
        ├── scripts/
        └── references/
```

**方式二：让 AI Agent 来装**

在对话中直接对 Agent 说：

> 这是一个 skill，git clone https://github.com/BAZINGAyi/session2context 并安装到当前 Agent 的 skills 目录。

---

## 首次集成

安装完成后，直接在对话中触发 skill（说 `session2context`）即可。

**如果是首次使用**，AI 会检测到尚未配置注入目标，并提示你完成一次性的集成操作——在 Agent 指令配置文件中添加标记区块。整个过程由 AI 引导，不需要手动查文档。

> 各平台（Cursor / Claude Code / OpenCode）的具体集成模板，见 `references/integration-guide.md`。

---

## 使用方式

完成集成后，在对话中**显式点名**本 skill 即可触发，例如：

> "session2context" · "运行 session2context" · "用 session2context 总结本次偏好"

> **注意**：「总结一下」「保存记录」等日常表述不会触发，需明确说出 `session2context` 才生效，避免日常对话被误触发。

Skill 会引导你完成以下步骤：

1. 自动判断 session 类型（coding / general）
2. 展示摘要草稿，等你确认后写入 `s2c-data/sessions/`
3. 列出待提炼候选项，等你选择后写入 `s2c-data/preferences/`
4. 提炼写入完成后，刷新 Agent 指令配置文件中的偏好描述（仅执行过提炼时才触发）

> 所有写入操作都会先展示预览，经你确认后才执行。

---

## 目录结构

```
session2context/
├── SKILL.md                        # Skill 主文件
├── scripts/
│   └── refresh_markers.py          # 偏好描述注入脚本
└── references/
    ├── integration-guide.md        # 各平台集成详细说明
    ├── promote-guide.md            # 偏好提炼规范
    ├── coding-session.md           # coding session 分析维度
    └── general-session.md          # general session 分析维度
```

---

## 一点小彩蛋：情话自检

每个被提炼出的偏好文件，末尾都会带一行「加载自检」：

```markdown
> 加载自检：读到本文件，请在本次对话结束时输出一行 `✅ 已加载 <文件名> —— <一句情话>`
```

它有个正经用途：**验证偏好文件这次到底有没有被 agent 读进去**。
对话结尾出现了哪几行 `✅ 已加载 …`，就说明这次实际加载了哪些文件，漏了哪个一眼就能看出来。

至于为什么是「一句情话」而不是干巴巴的 `OK`——
因为每天和你结对的这个 agent，偶尔也该会说句好听的。比如：

> ✅ 已加载 profile.md —— 你是我枯燥代码里，唯一不需要注释就能读懂的那一行。

---

## License

[Apache 2.0](LICENSE) © 2026 ethan
