# TASK-0008：Chapter 03《Model Context》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 2 章、.ai/principles/architecture-map.md（第三层） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

编写 Part 02 第二章 `docs/02-agent-runtime/ch03-model-context.md`：回答"模型看到的到底是什么"——Runtime 如何把 State 与外部信息组装成一次模型调用。不写 Prompt Engineering / LangGraph API / Memory / Checkpoint / MCP / RAG。

## 需要新增

- `docs/02-agent-runtime/ch03-model-context.md`（3.1-3.9，回答 Q1-Q10，4 张 Mermaid 图）
- `.ai/tasks/TASK-0008-chapter-03-model-context.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Runtime 导航加入第 3 章）
- `docs/02-agent-runtime/index.md`（章节列表）
- `ROADMAP.md`（v0.3.0 Chapter 03 draft 勾选）
- `docs/00-introduction/content-map.md`（第 3 章行）
- `.ai/context/current.md`

## 约束

- 不定义新架构、不修改 architecture-map / principles / ADR、不新增概念
- 不提前讲 Prompt Builder / Memory / LangGraph API
- 不新增 Demo / Python；全部引用已有代码与 principles
- 面向读者讲解，不复制 principles；不成为新的单一事实源

## 验收标准

- [x] 章节结构 3.1-3.9 完成，Q1-Q10 全部回答
- [x] 4 张 Mermaid 图（State→Context / Builder 流程 / Prompt-Context-State 关系 / 生命周期）
- [x] `mkdocs build --strict`、`pytest`、`ruff check .` 通过
- [x] PR #14 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（六项修正：Context 变化来源 / 控制字段派生进入 / Prompt 术语表 / 生命周期逻辑周期 / 模型-Builder 边界 / Context Contract 测试条件）
- [x] PR #14 squash merge 到 main（commit 21af67f），远程 feature/chapter-03-model-context 已删除
- 合并后方可标记 completed（本次已合并）
