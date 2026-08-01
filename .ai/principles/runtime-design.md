# Runtime Design Principles

## 1. 什么叫 Runtime

`TERMINOLOGY.md`：Agent Runtime 是负责执行 Agent Loop 的运行环境，包括状态、调度、工具、错误、Checkpoint、Interrupt、Streaming 和 Trace。

本项目两个 Runtime 的实现证明了这份职责清单的最小集合：

| 职责 | Manual Runtime（`runtime.py`） | LangGraph Runtime（`graph.py` + `nodes.py` + `routing.py`） |
|---|---|---|
| 生命周期 | `AgentStatus`：RUNNING / SUCCESS / FAILED / MAX_ITERATIONS_REACHED | 同一套 `AgentStatus`，写入 State |
| Loop | `while not state.is_terminal()` | 条件边回路（动作节点 → route_decide_or_max → decide → route_by_next_action → 动作节点） |
| Dispatch | `_dispatch(action, state)` 按 ActionType 分发 | `route_by_next_action` 按 `next_action` 分发 |
| Error Boundary | try/except 包住整轮 → FAILED + failure_reason | 节点级 `_failure_boundary` + agent 层兜底 |
| Retry / Resume 挂载点 | 修复循环的调度位置（T04→T05→T07 回路） | 同一回路；Checkpoint 挂载点预留（未启用） |

## 2. 三层职责边界（谁负责什么）

**第 1 层：模型负责开放式语义决策。**

- `decide_next()`：下一步动作决策（GENERATE_SQL / FIX_SQL / FINALIZE）
- `generate_sql()` / `fix_sql()`：SQL 内容生成与修复（repair）

开放式语义决策没有确定答案，必须交给模型——PR #4 Architecture Review Blocker 1 直接强制了这条规则：basic_langgraph 第一版让路由函数根据校验结果决定 generate / fix / finalize（模型没有参与决策），Review 判定为与手写版**不等价**。修复后 `decide` 节点调用 `model.decide_next()`，路由函数只做分发。

**第 2 层：确定性策略层负责安全与治理决策。**

- 权限、安全、预算、超时、审批、终止、补偿

这些决策**必须由代码拥有**（ADR-004：确定性约束优先由代码保证；`AGENTS.md` 安全底线）。本项目已实现的最小集合：终止（`route_decide_or_max` 的上限检查先于模型决策执行）、SQL 安全（`FakeSQLValidator` / `FakeSQLExecutor` 的纵深防御独立实现）。权限 / 预算 / 审批 / 补偿属于 canonical T06 与 v0.6.0 里程碑，是确定性策略层的扩展点。

**第 3 层：Runtime 负责控制机制。**

- 调度、Loop、State、Dispatch、Error Boundary、Retry / Resume 挂载点

**边界结论：**

- Runtime **不得替代模型**完成开放式语义决策（PR #4 Blocker 1）
- 但代码**必须拥有**确定性安全与治理决策（ADR-004）——"终止由代码保证"与"下一步动作由模型决定"不冲突：上限检查先于模型决策执行，检查不通过就不调用模型

## 3. 为什么 Loop 必须属于 Runtime

一一对照（完整映射见 `docs/03-langgraph-core/manual-vs-langgraph.md` 第 1 节）：

| 手写 | LangGraph |
|---|---|
| `while not state.is_terminal()` | 条件边回路 + 终止状态守卫 |
| `decide_next()` 的 if/elif | `decide` 节点 + `route_by_next_action` |
| 循环顶部上限检查 | `route_decide_or_max` |
| `is_terminal()` 终止 | `finalize`→END / `max_iterations`→END / 终止状态守卫 |

原因：

1. **循环需要确定性终止**：`max_iterations` 兜底是确定性策略层的职责（ADR-004）。模型无法承诺终止——若循环属于模型，就失去了确定性兜底，`test_max_iterations_2_stops_before_finalize` 这类断言将无从谈起。
2. **循环是故障隔离的边界**：manual 的 try/except 包住整轮（`runtime.py`）、graph 的节点级异常转换（`_failure_boundary`）——失败处理必须知道"这一轮"的边界，而轮次由 Runtime 定义。
3. **循环载体可以替换**：TASK-0003 证明 while → 图，业务代码与模型零改动（复用 `FakeLLM` / Validator / Executor）。如果循环逻辑散落在业务 / 模型代码里，这种替换不可能。

## 4. Runtime 可以改变，业务不能改变

已验证的事实（TASK-0003）：

- `while`（`runtime.py`）→ LangGraph（`graph.py`）——**Runtime 载体可以变**。
- `FakeLLM` / `FakeSQLValidator` / `FakeSQLExecutor` 与业务规则（语义层、SQL 安全底线、权限、审计）——**不能变**。

原因：Runtime 提供的是控制原语（Loop、Retry、Iteration、Checkpoint 的挂载点）；确定性策略层提供安全与治理约束；业务提供领域约束（口径、语义）。ADR-003 记录"LangGraph 是核心实践框架，但不是唯一主题"——正是"Runtime 可替换"的决策。`AGENTS.md` 安全底线与 ADR-004 / ADR-005 记录"业务约束由业务系统保证"——正是"业务不能变"的决策。

后续可验证方向（**待验证，不作为已验证证据**）：Temporal / Durable Execution / Workflow Engine 等其他 Durable Execution Runtime 是否能在保持业务契约不变的前提下替换当前 Runtime。
