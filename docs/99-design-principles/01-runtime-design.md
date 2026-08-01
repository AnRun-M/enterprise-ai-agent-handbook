# Runtime Design Principles

## 1. 什么叫 Runtime

`TERMINOLOGY.md`：Agent Runtime 是负责执行 Agent Loop 的运行环境，包括状态、调度、工具、错误、Checkpoint、Interrupt、Streaming 和 Trace。

本项目两个 Runtime 的实现证明了这份职责清单的最小集合：

| 职责 | Manual Runtime（`runtime.py`） | LangGraph Runtime（`graph.py` + `nodes.py` + `routing.py`） |
|---|---|---|
| 生命周期 | `AgentStatus`：RUNNING / SUCCESS / FAILED / MAX_ITERATIONS_REACHED | 同一套 `AgentStatus`，写入 State |
| Loop | `while not state.is_terminal()` | 条件边回路（动作节点 → route_decide_or_max → decide → route_by_next_action → 动作节点） |
| Max Iteration | 循环顶部 `iteration >= max_iterations` 检查 | `route_decide_or_max` 确定性检查（先于模型决策执行） |
| Dispatch | `_dispatch(action, state)` 按 ActionType 分发 | `route_by_next_action` 按 `next_action` 分发 |
| Error Boundary | try/except 包住整轮 → FAILED + failure_reason | 节点级 `_failure_boundary` + agent 层兜底 |

**Runtime 永远不负责业务决策。** 这是 PR #4 Architecture Review Blocker 1 直接强制出来的规则：basic_langgraph 第一版的路由函数直接根据 State（校验是否通过）决定 generate / fix / finalize，Review 判定为与手写版**不等价**——因为手写版的决策来自 `model.decide_next()`。修复后：`decide` 节点调用模型，路由函数只做两件事（确定性上限检查、按 next_action 分发）。

## 2. 什么属于 Model

模型负责：

- `decide_next()`：下一步动作决策（GENERATE_SQL / FIX_SQL / FINALIZE）
- `generate_sql()` / `fix_sql()`：SQL 内容生成

模型不负责（两个 Runtime 代码的事实，`FakeLLM` 是同一个类）：

- **Loop**：while 与条件边回路都不在 `models.py`
- **Retry**：修复循环的迭代控制由 Runtime 决定（T04 → T05 → T07 回路）
- **Iteration**：iteration 递增在 manual 的循环顶部（`runtime.py`）与 graph 的 `decide` 节点（`nodes.py`）——都由代码执行
- **History**：`record_round`（manual）/ reducer 追加（graph）——都不在模型里

证据：两个 Runtime 共享**同一个** `FakeLLM`（TASK-0003 复用而非复制）。如果 Loop / Iteration / History 属于模型，这种复用不可能成立。

## 3. 为什么 Loop 必须属于 Runtime

一一对照（完整映射见 `docs/03-langgraph-core/manual-vs-langgraph.md` 第 1 节）：

| 手写 | LangGraph |
|---|---|
| `while not state.is_terminal()` | 条件边回路 + 终止状态守卫 |
| `decide_next()` 的 if/elif | `decide` 节点 + `route_by_next_action` |
| 循环顶部上限检查 | `route_decide_or_max` |
| `is_terminal()` 终止 | `finalize`→END / `max_iterations`→END / 终止状态守卫 |

原因：

1. **循环需要确定性终止**：`max_iterations` 兜底是代码保证的（ADR-004：确定性约束优先由代码保证）。模型无法承诺终止——若循环属于模型，就失去了确定性兜底，`test_max_iterations_2_stops_before_finalize` 这类断言将无从谈起。
2. **循环是故障隔离的边界**：manual 的 try/except 包住整轮（`runtime.py`）、graph 的节点级异常转换（`_failure_boundary`）——失败处理必须知道"这一轮"的边界，而轮次由 Runtime 定义。
3. **循环载体可以替换**：TASK-0003 证明 while → 图，业务代码与模型零改动。如果循环逻辑散落在业务 / 模型代码里，这种替换不可能。

## 4. Runtime 可以改变，业务不能改变

已验证的事实（TASK-0003）：

- `while`（`runtime.py`）→ LangGraph（`graph.py`）→ 未来可替换为 Temporal / Durable Execution / Workflow Engine——**Runtime 载体可以变**。
- `FakeLLM` / `FakeSQLValidator` / `FakeSQLExecutor` 与业务规则（语义层、SQL 安全底线、权限、审计）——**不能变**。

原因：Runtime 提供的是控制原语（Loop、Retry、Iteration、Checkpoint 的挂载点）；业务提供的是领域约束（谁能查什么、SQL 怎么算安全、口径怎么定义）。ADR-003 记录"LangGraph 是核心实践框架，但不是唯一主题"——正是"Runtime 可替换"的决策。`AGENTS.md` 安全底线与 ADR-004 / ADR-005 记录"业务约束由业务系统保证"——正是"业务不能变"的决策。
