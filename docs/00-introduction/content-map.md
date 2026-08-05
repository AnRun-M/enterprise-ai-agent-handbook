# 章节—示例—测试映射

本文是章节、示例、测试之间追踪关系的唯一来源，随 ROADMAP 演进更新。

| 章节 | 核心概念 | 对应示例 | 对应测试 | 当前状态 | 目标版本 |
|---|---|---|---|---|---|
| 第 0 章：你已经写了一个 Agent | Agent 最小闭环、手写 Runtime、框架价值 | `examples/manual_agent_loop`、`examples/basic_langgraph` | 手写 Loop 测试 | 最终完成 | v0.2.0 |
| 第 1 章：Agent Loop | Observe / Decide / Act / Update State、终止（Success/Failure/Max Iteration/Human Stop）、Retry vs Loop、Workflow vs Agent | `examples/manual_agent_loop`、`examples/basic_langgraph` | 手写 Loop 测试、max_iterations off-by-one | 最终完成 | v0.3.0 |
| 第 2 章：Execution State | 唯一控制事实源、State 生命周期与演化、进入与不进入、Schema 契约 | `examples/manual_agent_loop`、`examples/basic_langgraph` | State reducer、等价对照、failure_reason 三场景 | 最终完成 | v0.3.0 |
| 第 3 章：Model Context | 一次调用可见输入、State→Context 切片、Prompt 是 Context 组件、Context Builder 归属 | `examples/manual_agent_loop`、`examples/basic_langgraph` | 等价对照 | 最终完成 | v0.3.0 |
| 第 4 章：Prompt Builder | 组装为最终 Model Context、Template→Instance→Context、Prompt 版本契约、Builder 属于 Runtime | `examples/manual_agent_loop`、`examples/basic_langgraph` | 等价对照 | 最终完成 | v0.3.0 |
| 第 5 章：Tool Registry | 能力描述与执行映射、Definition/Handler 分离、Dispatch 三职责、权限纵深防御、schema 版本、Result Contract | `examples/manual_agent_loop`、`examples/basic_langgraph` | 等价对照 | 最终完成 | v0.3.0 |
| 第 6 章：Runtime Scheduler & Orchestration | Loop / Routing / Lifecycle Guard 边界、可执行步骤 / work item 调度、Runtime Control Plane 编排、Scheduler / Policy / LLM 职责边界、Runtime 替换契约与教学 Demo 验证范围 | `examples/manual_agent_loop`、`examples/basic_langgraph` | 路由纯函数、等价对照、max_iterations | 最终完成 | v0.3.0 |
| Part 2：Agent Runtime（Execution State / Model Context / Prompt Builder / Tool Registry / Runtime Scheduler & Orchestration / Memory、Context 与 Context Management） | 框架无关 Runtime 语义、状态与上下文、模型输入组装、能力管理、执行编排、上下文生命周期 | `examples/manual_agent_loop`、`examples/basic_langgraph` | State transition、路由决策、双 Runtime 行为等价 | 最终完成（Chapter 02-07 全部完成，2026-08-01） | v0.3.0 |
| 第 7 章：Memory、Context 与 Context Management | Memory 与 State/Context/Checkpoint 边界、Context Window、History、Compression/Trimming/Summarization、Injection、生命周期与事实源 | 待规划 | 待规划 | 最终完成 | v0.3.0 |
| Part 3：LangGraph Core（StateGraph / Node / Edge / Conditional Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream / Subgraph） | 图运行时、恢复、流式 | `examples/basic_langgraph` | Graph path、Checkpoint recovery | 进行中（示例与等价 Demo 已完成；第 8/9 章最终完成，第 10 章正文初稿） | v0.4.0 |
| 第 8 章：为什么是图——为什么 Runtime 可以用 Graph 表达 | 执行控制结构可图化（循环显式 / 连接可声明 / 执行结构可审查）、Graph Representation vs LangGraph Runtime（集成点 ≠ 能力自动生效）、执行控制关切图化范围、图带来与没带来、适用边界 | `examples/basic_langgraph`（README 16/17/18 节） | 双 Runtime 行为等价（`test_direct_equivalence_with_manual`） | 最终完成（2026-08-05，PR #27） | v0.4.0 |
| 第 9 章：Graph State——状态如何进入图 | Execution State 的 LangGraph 承载：schema 定义图（字段名 / 类型 / 更新形状 / reducer 挂载点）、TypedDict 定位（当前 Demo 选择非唯一方案）、Initial State、START / END 图结构哨兵、节点部分更新、与 Context / Memory / Checkpoint 边界 | `examples/basic_langgraph`（state.py / graph.py / nodes.py / agent.py） | Initial State 完整性（`test_initial_state_complete`）、路由纯函数、双 Runtime 行为等价 | 最终完成（2026-08-05，PR #29） | v0.4.0 |
| 第 10 章：Execution Nodes——Node 执行模型 | Graph Runtime 管理的执行单元（读 State → 执行能力 → 返回部分更新 → Runtime 合并 → 下一执行步骤）、节点生命周期、LLM / Tool / Pure Compute 三类节点、节点级 Failure Boundary、Node ≠ Tool / ≠ Python function / ≠ Runnable | `examples/basic_langgraph`（nodes.py / graph.py / agent.py） | 错误边界（`test_model_exception_saves_failure_reason` / `test_fix_exception_preserves_state_and_history`）、模型决策路由、双 Runtime 行为等价 | 实现完成 / 待架构审查 | v0.4.0 |
| Part 4：Text-to-SQL 重构（Text2SQLState / 意图识别 / 元数据与业务规则检索 / SQL 生成 / SQL 校验 / 权限检查 / 引擎路由 / SQL 修复循环 / Python 分析 / 结构化输出） | 全流程落地 | `examples/text2sql_state`、`examples/sql_validation` | SQL validator、Router、Text-to-SQL regression | 规划 | v0.5.0 |
| Part 5：生产级能力（Checkpoint / HITL / 幂等 / Retry / Timeout / Compensation / Observability / Cost Control / Evaluation / Regression Test） | 可靠性、可观测、评测 | `examples/checkpoint_hitl` | Checkpoint recovery | 规划 | v0.6.0 |
| Part 6：MCP 与 A2A（MCP 边界 / MCP Tool 接入 / A2A 边界 / Agent Card / Task / Artifact / 服务化） | 能力连接与 Agent 协作标准 | 待规划 | Tool adapter | 规划 | v0.7.0 |
| Part 7：AI Coding | 审查 AI 生成的 Agent 代码 | 待规划 | 待规划 | 规划 | v1.0.0 |

## 约定

- 「对应示例」指向 `examples/` 下的目录名；「对应测试」指向 `tests/README.md` 规划的测试目标。
- 「目标版本」与 `ROADMAP.md` 里程碑一致。
- 部分示例横跨多个章节时，以「首次深入讲解」所在章节为准。
- 「当前状态」统一使用四种状态，不出现其他状态名称：`规划` → `进行中` → `实现完成 / 待架构审查` → `最终完成`。
