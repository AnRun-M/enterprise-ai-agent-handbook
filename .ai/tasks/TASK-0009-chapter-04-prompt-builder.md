# TASK-0009：Chapter 04《Prompt Builder》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 3 章（Model Context）、.ai/principles/architecture-map.md（第三层） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

编写 Part 02 第三章 `docs/02-agent-runtime/ch04-prompt-builder.md`：回答"Runtime 为什么需要 Prompt Builder"。**不是 Prompt Engineering**——不谈技巧 / Few-shot / CoT。Builder 是 Runtime 的一个组件，负责把各种输入稳定组装成一次模型调用的最终 Model Context。

## 需要新增

- `docs/02-agent-runtime/ch04-prompt-builder.md`（4.1-4.9，回答 Q1-Q10，4 张 Mermaid 图）
- `.ai/tasks/TASK-0009-chapter-04-prompt-builder.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Runtime 导航加入第 4 章）
- `docs/02-agent-runtime/index.md`（章节列表）
- `ROADMAP.md`（v0.3.0 Chapter 04 draft 勾选）
- `docs/00-introduction/content-map.md`（第 4 章行）
- `.ai/context/current.md`

## 约束

- 不提前展开 Memory / Checkpoint / Interrupt / Reducer / LangGraph API / RAG / MCP / A2A / Observability / Evaluation（仅标记边界与挂载点）
- Demo 无显式 Builder 必须标注"Runtime 的逻辑抽象，目前 Demo 为隐式实现"，不把推论写成事实
- 不新增 Demo / Python；统一引用第 1/2/3 章与 principles，不复制定义

## 验收标准

- [x] 章节结构 4.1-4.9 完成，Q1-Q10 全部回答
- [x] 4 张 Mermaid 图（Builder 位置 / 输入来源 / 输出到 Context / Version 生命周期）
- [x] `mkdocs build --strict`、`pytest`、`ruff check .` 通过
- [x] PR #16 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（六项修正：Builder 输出表述 / Policy-Builder 边界 / 行为契约与数据契约区分 / 两类测试分离 / 审计最小集合 / RAG 挂载点收窄）
- [x] PR #16 squash merge 到 main（commit 4be82e2），远程 feature/chapter-04-prompt-builder 已删除
- 合并后方可标记 completed（本次已合并）
