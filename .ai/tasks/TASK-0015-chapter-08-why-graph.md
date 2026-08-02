# TASK-0015：Chapter 08《为什么是图：为什么 Runtime 可以用 Graph 表达》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-03 |
| Updated | 2026-08-03 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 1 章（Loop）、第 2 章（Execution State）、第 6 章（Scheduler & Orchestration）、第 7 章；TASK-0014（Part 03 规划） |
| Related Example | examples/basic_langgraph（README 第 16/17/18 节）、examples/manual_agent_loop |
| Related Test | tests/basic_langgraph（`test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 定位章 `docs/03-langgraph-core/ch08-why-graph.md`：回答「**为什么 Runtime 可以用 Graph 表达**」这一前置问题，为后续原语章（ch09-ch17）提供统一的思考框架。**不承担索引职责**（Runtime → LangGraph 映射表是 Part 03 全局参考，不属于本章正文）。

## 需要新增

- `docs/03-langgraph-core/ch08-why-graph.md`（8.1-8.9 结构，回答 Q1-Q10，4 张 Mermaid 图）
- `.ai/tasks/TASK-0015-chapter-08-why-graph.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 8 章）
- `docs/03-langgraph-core/index.md`（章节列表 + 第 8 章条目）
- `docs/00-introduction/content-map.md`（新增第 8 章行，状态「进行中/正文初稿」）
- `ROADMAP.md`（v0.4.0 标注 Chapter 08 draft）
- `.ai/context/current.md`

## 约束

- **只回答「LangGraph 如何承载 Runtime」**：Runtime 第一视角、Framework 第二视角；先解释 Runtime 语义，再解释 LangGraph 如何实现；禁止从 API 出发解释概念
- **禁止重新定义** State / Context / Memory / Scheduler / Tool Registry——只能引用 Part 02 章节（ch01/ch02/ch06/ch07 与 architecture-map）
- 不复制 Runtime → LangGraph 映射表（全局参考）；不介绍任何单个 LangGraph API 的写法（ch09-ch17 职责）
- 不提前讲 Part 05 生产语义（Checkpoint/Interrupt/Stream 只作为挂载点提及）、不涉及 MCP/A2A
- Demo 如实标注：Checkpoint / Interrupt / Stream / Send / Command / Subgraph 在 basic_langgraph 均未使用
- 遵守 ADR-0001（先动机后 API）、ADR-0003（LangGraph 是核心框架但不是唯一主题）、architecture-map（Part 01-03 归属）、runtime-design（三层职责）、state-design（State 边界）
- 术语与 `TERMINOLOGY.md` 一致（首次出现「中文（English）」）；流程引用 canonical-pipeline / manual-vs-langgraph

## 验收标准

- [x] 章节结构 8.1-8.9 完成，Q1-Q10 全部回答
- [x] 主线明确：Runtime 的可图化源于控制流三个性质（循环显式、连接可声明、边界可挂载）
- [x] 每节先 Runtime 语义后 LangGraph 承载，无 API 先行的解释
- [x] 4 张 Mermaid 图（while vs 图回路 / 边界可挂载 / 图带来与没带来 / Runtime 章节→图原语概念映射）
- [x] `mkdocs build --strict`、`git diff --check`、`pytest`（57 passed）、`ruff check .` 通过
- [x] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] 创建 PR 等待 Architecture Review（不 Merge）
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-03：任务创建，开始正文初稿。
- 2026-08-03：正文初稿完成 `docs/03-langgraph-core/ch08-why-graph.md`（8.1-8.9，Q1-Q10，4 张 Mermaid 图）；四源更新完成；mkdocs build --strict / git diff --check / pytest 57 passed / ruff 全过。待创建 PR 进入 Architecture Review。
