# TASK-0005：Chapter 01《Agent Loop》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 0 章、.ai/principles/ |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

编写本书第一章 `docs/01-agent-foundations/ch01-agent-loop.md`：回答"Agent 为什么必须有 Loop？Loop 在 Runtime 中承担什么职责？"，建立整个 Runtime 世界观。不是 LangGraph 教程、不是 Prompt Engineering、不写 StateGraph / Node / Edge / Pregel（属于 Part 3）。

## 需要新增

- `docs/01-agent-foundations/ch01-agent-loop.md`（正文，1.1 ~ 1.9，4 张 Mermaid 图，回答 Q1-Q10）
- `.ai/tasks/TASK-0005-chapter-01-agent-loop.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Foundations 导航加入第 1 章）
- `docs/01-agent-foundations/index.md`（章节列表加入第 1 章）
- `ROADMAP.md`（v0.3.0 勾选 Chapter 01 draft）
- `docs/00-introduction/content-map.md`（新增第 1 章行）
- `.ai/context/current.md`

## 约束

- 全部引用已有产物：ADR、.ai/principles/、两个 Runtime 代码、canonical pipeline
- 禁止新增 Demo 与 Python 代码；禁止介绍 LangGraph API / 图机制
- 写作目标：读者从未听过 LangGraph，读完也能自己写出 while True Agent Loop

## 验收标准

- [x] 章节结构 1.1-1.9 完成，Q1-Q10 全部回答
- [x] 4 张 Mermaid 图（四阶段闭环 / pipeline 位置 / Manual↔Graph 映射 / 终止状态机）
- [x] `mkdocs build --strict` 通过
- [x] `pytest`、`ruff check .` 通过
- [x] PR #8 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（三项概念修正：状态转换过程严格表述 / Workflow vs Agent 判据重写为决策权归属 / Human Stop 改为暂停态）
- [x] PR #8 squash merge 到 main（commit e63e7df），远程 feature/chapter-01-agent-loop 已删除
- 合并后方可标记 completed（本次已合并）
