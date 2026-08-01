# 章节—示例—测试映射

本文是章节、示例、测试之间追踪关系的唯一来源，随 ROADMAP 演进更新。

| 章节 | 核心概念 | 对应示例 | 对应测试 | 当前状态 | 目标版本 |
|---|---|---|---|---|---|
| 第 0 章：你已经写了一个 Agent | Agent 最小闭环、手写 Runtime、框架价值 | `examples/manual_agent_loop`、`examples/basic_langgraph` | 手写 Loop 测试 | 最终完成 | v0.2.0 |
| 第 1 章：Agent Loop | Observe / Decide / Act / Update State、终止（Success/Failure/Max Iteration/Human Stop）、Retry vs Loop、Workflow vs Agent | `examples/manual_agent_loop`、`examples/basic_langgraph` | 手写 Loop 测试、max_iterations off-by-one | 最终完成 | v0.3.0 |
| 第 2 章：Execution State | 唯一控制事实源、State 生命周期与演化、进入与不进入、Schema 契约 | `examples/manual_agent_loop`、`examples/basic_langgraph` | State reducer、等价对照、failure_reason 三场景 | 最终完成 | v0.3.0 |
| 第 3 章：Model Context | 一次调用可见输入、State→Context 切片、Prompt 是 Context 组件、Context Builder 归属 | `examples/manual_agent_loop`、`examples/basic_langgraph` | 等价对照 | 最终完成 | v0.3.0 |
| 第 4 章：Prompt Builder | 组装为最终 Model Context、Template→Instance→Context、Prompt 版本契约、Builder 属于 Runtime | `examples/manual_agent_loop`、`examples/basic_langgraph` | 等价对照 | draft / 待架构审查 | v0.3.0 |
| Part 2：Agent Runtime（LLM 与 Agent / Agent Loop / Runtime / State / Tool Registry / Prompt Builder / Memory 与 Context / 手写 Runtime） | Runtime 概念、State 生命周期 | `examples/manual_agent_loop` | State reducer、Tool adapter | 进行中（Execution State 已完成） | v0.3.0 |
| Part 3：LangGraph Core（StateGraph / Node / Edge / Conditional Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream / Subgraph） | 图运行时、恢复、流式 | `examples/basic_langgraph` | Graph path、Checkpoint recovery | 进行中（示例与等价 Demo 已完成，正文待写） | v0.4.0 |
| Part 4：Text-to-SQL 重构（Text2SQLState / 意图识别 / 元数据与业务规则检索 / SQL 生成 / SQL 校验 / 权限检查 / 引擎路由 / SQL 修复循环 / Python 分析 / 结构化输出） | 全流程落地 | `examples/text2sql_state`、`examples/sql_validation` | SQL validator、Router、Text-to-SQL regression | 规划 | v0.5.0 |
| Part 5：生产级能力（Checkpoint / HITL / 幂等 / Retry / Timeout / Compensation / Observability / Cost Control / Evaluation / Regression Test） | 可靠性、可观测、评测 | `examples/checkpoint_hitl` | Checkpoint recovery | 规划 | v0.6.0 |
| Part 6：MCP 与 A2A（MCP 边界 / MCP Tool 接入 / A2A 边界 / Agent Card / Task / Artifact / 服务化） | 能力连接与 Agent 协作标准 | 待规划 | Tool adapter | 规划 | v0.7.0 |
| Part 7：AI Coding | 审查 AI 生成的 Agent 代码 | 待规划 | 待规划 | 规划 | v1.0.0 |

## 约定

- 「对应示例」指向 `examples/` 下的目录名；「对应测试」指向 `tests/README.md` 规划的测试目标。
- 「目标版本」与 `ROADMAP.md` 里程碑一致。
- 部分示例横跨多个章节时，以「首次深入讲解」所在章节为准。
- 「当前状态」统一使用四种状态，不出现其他状态名称：`规划` → `进行中` → `实现完成 / 待架构审查` → `最终完成`。
