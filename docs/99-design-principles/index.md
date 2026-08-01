# Agent Runtime Design Principles（项目宪法）

> 本文档集**不是面向读者的章节**，而是本项目的 **Constitution（宪法）**：所有未来章节、代码、Demo 与 PR Review 必须服从的统一设计规范。

## 为什么存在

本仓库已经完成两条证据链：

- **手写 Runtime**：`examples/manual_agent_loop`（PR #2，含两轮 Architecture Review）
- **LangGraph 等价 Runtime**：`examples/basic_langgraph`（PR #4，含 Architecture Review）

这些代码与 Review 中反复出现的设计判断，本应沉淀为规范。本文档集就是把**已经验证过的事实**固化为**以后必须遵守的规则**——它不是预测，是记录。

## 来源约束

每一条原则都必须能引用已有产物：

- 第 0 章（`docs/01-agent-foundations/ch00-you-already-built-an-agent.md`）
- Manual Runtime 代码（`examples/manual_agent_loop/`）
- LangGraph Runtime 代码（`examples/basic_langgraph/`）
- PR / Architecture Review 结论
- ADR-0001 ~ ADR-0006

**禁止**：新增本仓库尚未验证过的理论；使用"我认为 / 最佳实践 / 推荐"式表述。这是一本工程书，不是论文。

## 为什么这不是读者章节

`ARCHITECTURE.md` 内容边界：`docs/` 是正式出版内容。但本文档集的读者是**写这本书的人**（作者、AI 协作者、Reviewer），不是**读这本书的人**。读者章节回答"怎么理解 Agent"；本集回答"本项目以后必须怎么写"。它优先于单章内容：任何章节或 Demo 与本集冲突时，以本集为准。

## 文档地图

| 文档 | 回答的问题 | 直接来源 |
|---|---|---|
| [01-runtime-design.md](01-runtime-design.md) | Runtime 的职责边界在哪 | manual_agent_loop / basic_langgraph / PR #4 Review |
| [02-state-design.md](02-state-design.md) | 为什么 State 是唯一事实来源 | AgentState / GraphState / PR #2 Review |
| [03-llm-vs-runtime.md](03-llm-vs-runtime.md) | LLM 与 Runtime 的边界在哪 | 第 0 章 / TASK-0003 / PR #4 Review |
| [04-testing-agent.md](04-testing-agent.md) | 为什么必须测 State Transition | tests/ 全部代码 / CI（tests.yml） |
| [05-review-checklist.md](05-review-checklist.md) | 每个 PR 必须审查什么 | PR #2 / PR #4 的真实 Review 结论 |
