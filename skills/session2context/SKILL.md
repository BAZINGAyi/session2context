---
name: session2context
compatibility: 需要 Python 3 环境及项目根目录读写权限（用于运行 scripts/refresh_markers.py）
description: 从当前 session 对话提取用户习惯与偏好信号，生成摘要并（经确认后）提炼为持久化偏好写入 s2c-data/。仅在用户显式指名调用时使用——明确说出 “session2context”、“运行 session2context”、“用 session2context 总结/提炼本次偏好” 等点名本 skill 的指令时触发；不要因 “总结一下”“保存记录” 等日常宽泛表述自动触发，以免干扰正常对话。
---

# session2context

从当前 session 的对话中提取个人习惯信号，写入 `s2c-data/sessions/` 作为原始摘要。
提炼到 `s2c-data/preferences/` 作为**独立的二步操作**，需用户确认后才写入。

> 所有数据均存放在**当前项目根目录**下的 `s2c-data/`（相对路径、自包含，不跨项目共享）。

## 目录结构

```
<项目根>/
└── s2c-data/
    ├── sessions/       ← 第一层：原始 session 摘要（自动生成，可删，低信噪比）
    └── preferences/    ← 第二层：提炼后的偏好（手动维护，传给 LLM，高信噪比）
        ├── profile.md        ← 行为契约：用户习惯与对 agent 的要求
        └── proj-overview.md  ← 项目知识：技术栈、命令、结构、约定
```

> `preferences/` **推荐固定为这 2 个文件**；分类标准、新建规则与内容质量约束以 [references/promote-guide.md](references/promote-guide.md) 为**唯一权威来源**。

---

## Step 1：判断 session 类型

回顾当前对话，判断本次 session 属于哪种类型：

- **coding**：主要在写代码、调试、重构、架构设计
- **general**：讨论、学习、研究、非技术问题、工具使用探索

根据类型加载对应的分析参考：
- coding → 阅读 [references/coding-session.md](references/coding-session.md)
- general → 阅读 [references/general-session.md](references/general-session.md)

> 如果 session 内容混合（如：边讨论设计边写代码），同时加载两个参考文件。

---

## Step 2：生成 session 摘要

按加载的参考文件中定义的维度，分析当前对话，生成摘要。

**文件命名**：`YYYY-MM-DD-<topic-slug>.md`（topic-slug 用 2-4 个英文单词描述，kebab-case）

**写入路径**：`s2c-data/sessions/<filename>.md`

写入前，先在对话中**展示摘要内容**，让用户确认无误后再写入文件。

---

## Step 3：询问是否进行提炼（独立步骤）

摘要写入完成后，输出：

```
✅ session 摘要已保存至 s2c-data/sessions/<filename>.md

---
本次摘要中发现以下「待提炼候选项」：
<逐条列出>

是否现在将其中的条目提炼到 s2c-data/preferences/ ？
（这是独立操作，会修改你的偏好文件，建议谨慎评估每一条）

回复 **"是"或选择条目编号** 继续，回复 **"否"** 跳过。
```

---

## Step 4：执行提炼（仅在用户明确确认后）

阅读 [references/promote-guide.md](references/promote-guide.md) 了解提炼规范。

操作流程：
1. 读取目标 `preferences/` 文件的**当前内容**
2. 在对话中展示**变更预览**（新增了什么、放在哪里）
3. 等待用户最终确认
4. 确认后写入，**每次只修改一个文件**，写入后再问下一个
5. 写入后确保该文件**末尾保留加载自检行**（格式见 promote-guide.md「加载自检行」）；缺失则补上。空桩 / 纯注释文件不加

---

## Step 5：刷新 Agent 指令配置（提炼完成后自动执行）

所有 preferences 文件写入完成后，用脚本完成确定性的注入操作。**描述文本由你（LLM）生成，文件枚举、目标查找与区块替换全部交给脚本**——不要手工编辑标记区块（容易误伤区块外内容）。

> ⚠️ **脚本路径**：下面的 `scripts/refresh_markers.py` 是**相对本 skill 目录**（即本 `SKILL.md` 同级）的路径，**不是**相对 cwd/项目根。请按本 skill 所在目录解析脚本路径再运行；`--root` 默认即 cwd（项目根，`s2c-data/` 所在处），无需指定。
> 若报 `No such file or directory`，是脚本路径解析错了（脚本随 skill 分发、一定存在、**无需创建**），按 skill 目录修正后重试。

1. 枚举有效的偏好文件（确定性，用脚本，避免臆造路径）：
   ```bash
   python3 scripts/refresh_markers.py list-prefs
   ```
   仅返回 `s2c-data/preferences/` 下**去除注释后仍非空**的 `.md` 文件相对路径。

2. 为上一步返回的**每个**文件生成一行描述：先**通读文件内容**（忽略「加载自检」行，不纳入描述），再以 `##` 小节名为骨架，概括出该文件涵盖什么 + 加载时机。要求**含义完整、不遗漏关键类别**，同时尽量精炼，不逐条复述细节（必要时可在括号里点到关键点）。格式：
   ```
   - `<文件相对路径>` — <以小节为骨架的完整概括>。<加载时机>。
   ```
   例：
   ```
   - `s2c-data/preferences/profile.md` — 涵盖沟通（中文交流）、协作流程（先预览结果再询问）等行为偏好。所有对话必读。
   ```

3. 确认注入目标（确定性，用脚本）。脚本按以下**优先级**查找，**三者互斥、总共只在第一个带标记的文件注入一处**：
   1. `.cursor/rules/session2context.mdc`
   2. 项目根目录 `CLAUDE.md`
   3. 项目根目录 `AGENTS.md`
   ```bash
   python3 scripts/refresh_markers.py find-target
   ```

4. 把第 2 步生成的描述列表通过 stdin 交给脚本注入（脚本只替换 `<!-- s2c:start -->` 与 `<!-- s2c:end -->` 之间的内容，区块外一字不动）：
   ```bash
   python3 scripts/refresh_markers.py inject <<'EOF'
   - `s2c-data/preferences/profile.md` — <描述>
   - `s2c-data/preferences/proj-overview.md` — <描述>
   EOF
   ```
   脚本成功后会打印实际被更新的文件路径。

5. 在对话中告知用户脚本更新了**哪个**文件，并展示更新后的描述列表。

> 若 `find-target` 返回空（没有任何带标记的目标文件），提示用户参考 `references/integration-guide.md` 完成首次集成配置（创建 `.cursor/rules/session2context.mdc`，或在 `CLAUDE.md` / `AGENTS.md` 中加入标记区块）。脚本**不会自动创建文件**。

---

## 注意事项

- 如果判断当前 session 内容较少，可以提示用户积累更多后再提取
- 摘要只记录客观观察到的信号，不做主观判断
- 绝不在未经用户确认的情况下修改 `preferences/` 下的任何文件
