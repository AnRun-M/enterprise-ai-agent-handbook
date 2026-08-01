# Agent Runtime Design Principles（项目宪法）

> 本规范集**不是出版内容**（`ARCHITECTURE.md` 内容边界：`.ai/` 不属于书籍正文），
> 而是本项目的 **Constitution（宪法）**：所有未来章节、代码、Demo 与 PR Review 必须服从的统一设计规范。

## 为什么存在

本仓库已经完成两条证据链：

- **手写 Runtime**：`examples/manual_agent_loop`（PR #2，含两轮 Architecture Review）
- **LangGraph 等价 Runtime**：`examples/basic_langgraph`（PR #4，含 Architecture Review）

这些代码与 Review 中反复出现的设计判断，本应沉淀为规范。本规范集就是把**已经验证过的事实**固化为**以后必须遵守的规则**——它不是预测，是记录。

## 来源约束

每一条原则都必须能引用已有产物：

- 第 0 章（`docs/01-agent-foundations/ch00-you-already-built-an-agent.md`）
- Manual Runtime 代码（`examples/manual_agent_loop/`）
- LangGraph Runtime 代码（`examples/basic_langgraph/`）
- PR / Architecture Review 结论
- ADR-0001 ~ ADR-0006

**禁止**：新增本仓库尚未验证过的理论；使用"我认为 / 最佳实践 / 推荐"式表述。这是一本工程书，不是论文。

## 为什么这不是读者章节

读者章节回答"怎么理解 Agent"；本规范集回答"本项目以后必须怎么写"。它的读者是**写这本书的人**（作者、AI 协作者、Reviewer），不是**读这本书的人**。它优先于单章内容：任何章节或 Demo 与本集冲突时，以本集为准。因此它位于 `.ai/`（项目记忆），不进入 MkDocs 文档站。

## 文档地图

| 文档 | 回答的问题 | 直接来源 |
|---|---|---|
| [runtime-design.md](runtime-design.md) | Runtime / 确定性策略层 / 模型的三层职责边界 | manual_agent_loop / basic_langgraph / PR #4 Review |
| [state-design.md](state-design.md) | 为什么 State 是执行控制状态的唯一事实来源 | AgentState / GraphState / PR #2 Review |
| [llm-vs-runtime.md](llm-vs-runtime.md) | LLM 与 Runtime 的边界在哪 | 第 0 章 / TASK-0003 / PR #4 Review |
| [testing-agent.md](testing-agent.md) | 为什么必须测 State Transition | tests/ 全部代码 / CI（tests.yml） |
| [review-checklist.md](review-checklist.md) | 每个 PR 按影响范围必须审查什么 | PR #2 / PR #4 的真实 Review 结论 |
| [architecture-map.md](architecture-map.md) | Part 01-03 全局坐标系：Runtime 分层、State/Context/Memory/Checkpoint 边界、章节归属、canonical 挂载 | 全部已有代码 / ADR / 本集文档 / 第 0-1 章 |

**阅读规则**：涉及 Runtime / State / Context / Memory / Checkpoint 的章节或代码任务，在阅读本 index 后**必须继续阅读 [architecture-map.md](architecture-map.md)**——它是 Part 01 ~ Part 03 的全局坐标系，防止概念边界漂移。
