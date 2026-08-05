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
| Part 3：LangGraph Core（StateGraph / Node / Edge / Conditional Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream / Subgraph） | 图运行时、恢复、流式 | `examples/basic_langgraph` | Graph path、Checkpoint recovery | 进行中（示例与等价 Demo 已完成；第 8/9/10/11/12/13/14 章最终完成，第 15 章规划中） | v0.4.0 |
| 第 8 章：为什么是图——为什么 Runtime 可以用 Graph 表达 | 执行控制结构可图化（循环显式 / 连接可声明 / 执行结构可审查）、Graph Representation vs LangGraph Runtime（集成点 ≠ 能力自动生效）、执行控制关切图化范围、图带来与没带来、适用边界 | `examples/basic_langgraph`（README 16/17/18 节） | 双 Runtime 行为等价（`test_direct_equivalence_with_manual`） | 最终完成（2026-08-05，PR #27） | v0.4.0 |
| 第 9 章：Graph State——状态如何进入图 | Execution State 的 LangGraph 承载：schema 定义图（字段名 / 类型 / 更新形状 / reducer 挂载点）、TypedDict 定位（当前 Demo 选择非唯一方案）、Initial State、START / END 图结构哨兵、节点部分更新、与 Context / Memory / Checkpoint 边界 | `examples/basic_langgraph`（state.py / graph.py / nodes.py / agent.py） | Initial State 完整性（`test_initial_state_complete`）、路由纯函数、双 Runtime 行为等价 | 最终完成（2026-08-05，PR #29） | v0.4.0 |
| 第 10 章：Execution Nodes——Node 执行模型 | Graph Runtime 管理的执行单元（读 State → 执行能力 → 返回更新 → Runtime 合并 → 下一执行步骤）、四类节点形态（Semantic Decision / Mixed Capability / External Execution / Deterministic Compute）、节点级 Failure Boundary（应用实现）、Node ≠ Tool / ≠ Python function / ≠ Runnable | `examples/basic_langgraph`（nodes.py / graph.py / agent.py） | 错误边界（`test_model_exception_saves_failure_reason` / `test_fix_exception_preserves_state_and_history`）、模型决策路由、双 Runtime 行为等价 | 最终完成（2026-08-05，PR #31） | v0.4.0 |
| 第 11 章：Edge 与 Conditional Edge——静态边与条件路由 | Edge 确定性连接 / Conditional Edge 运行时选路、Route Decision（纯函数化，工程选择）与 Scheduling Execution（Graph Runtime 解释与调度）、模型决策写入 State 后由确定性路由分发（避免路由层替代模型）、route_decide_or_max = Lifecycle Guard + 上限检查（先于模型动作）、route_by_next_action 只分发、START/END 哨兵与连接 | `examples/basic_langgraph`（graph.py / routing.py） | 路由纯函数、max_iterations off-by-one、模型决策路由、双 Runtime 行为等价（`test_direct_equivalence_with_manual`） | 最终完成（2026-08-05，PR #33） | v0.4.0 |
| 第 12 章：Reducer——状态合并语义 | State Update → Reducer → Merged State 链路、默认覆盖 vs 追加语义（取决于 channel 数据契约）、Reducer 绑定 State channel 更新语义、Node / Reducer / Graph Runtime 三方职责、Reducer 不是业务决策器 / 路由器 / Scheduler / 并发控制器 | `examples/basic_langgraph`（state.py / nodes.py） | reducer 无重复追加（`test_history_reducer_appends_without_duplicates` / `test_reducer_semantics_operator_add`）、history 保留、双 Runtime 观察等价 | 最终完成（2026-08-05，PR #35） | v0.4.0 |
| 第 13 章：Command 与 Send——动态控制流 | Command：节点结果同时携带 State Update 与路由意图（更新与导航绑定）；Send：按运行时数据动态创建多个 work item（fan-out / map-reduce）；两者是不同动态控制流原语（不混同、Send ≠ Conditional Edge）；与 ch06 Scheduler / work item 调度对应；静态图足够时不需要动态原语 | `examples/basic_langgraph`（README 第 9 节：刻意未使用） | 无（Demo 未使用，如实标注；证据为官方核验记录） | 最终完成（2026-08-05，PR #37） | v0.4.0 |
| 第 14 章：Checkpoint——持久化与恢复 | 执行时刻的状态与执行上下文快照（非简单 State 字典副本）、Checkpointer 写入 / 读取 / 组织检索 / 列举并保存恢复所需 pending writes（恢复策略 / 重放语义 / 续跑规则由 Runtime 与应用契约决定）、恢复 / 重放 / 续跑、持久化内容（State channel values 含 Reducer 归并结果、next 执行位置、thread 标识、metadata、父快照关系及任务信息）、≠ Memory、当前 Demo 未启用（教学边界） | `examples/basic_langgraph`（未启用，docstring 教学边界）、`examples/checkpoint_hitl`（预留） | 无（未启用，如实标注；证据为 docstring / 官方核验记录） | 最终完成（2026-08-05，PR #39） | v0.4.0 |
| Part 4：Text-to-SQL 重构（Text2SQLState / 意图识别 / 元数据与业务规则检索 / SQL 生成 / SQL 校验 / 权限检查 / 引擎路由 / SQL 修复循环 / Python 分析 / 结构化输出） | 全流程落地 | `examples/text2sql_state`、`examples/sql_validation` | SQL validator、Router、Text-to-SQL regression | 规划 | v0.5.0 |
| Part 5：生产级能力（Checkpoint / HITL / 幂等 / Retry / Timeout / Compensation / Observability / Cost Control / Evaluation / Regression Test） | 可靠性、可观测、评测 | `examples/checkpoint_hitl` | Checkpoint recovery | 规划 | v0.6.0 |
| Part 6：MCP 与 A2A（MCP 边界 / MCP Tool 接入 / A2A 边界 / Agent Card / Task / Artifact / 服务化） | 能力连接与 Agent 协作标准 | 待规划 | Tool adapter | 规划 | v0.7.0 |
| Part 7：AI Coding | 审查 AI 生成的 Agent 代码 | 待规划 | 待规划 | 规划 | v1.0.0 |

## 约定

- 「对应示例」指向 `examples/` 下的目录名；「对应测试」指向 `tests/README.md` 规划的测试目标。
- 「目标版本」与 `ROADMAP.md` 里程碑一致。
- 部分示例横跨多个章节时，以「首次深入讲解」所在章节为准。
- 「当前状态」统一使用四种状态，不出现其他状态名称：`规划` → `进行中` → `实现完成 / 待架构审查` → `最终完成`。
