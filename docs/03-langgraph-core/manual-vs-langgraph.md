# 手写 Runtime vs LangGraph：一一对照

> 本文是 Part 3 的对照速览，不是完整教程。完整章节在 v0.4.0 里程碑展开。
> 对应实现：`examples/manual_agent_loop/`（手写）与 `examples/basic_langgraph/`（Graph）。
> 行为等价由 `tests/basic_langgraph/test_langgraph_agent.py` 证明。

## 1. 逐项映射表

| 手写 Runtime（manual_agent_loop） | LangGraph（basic_langgraph） | 文件 |
|---|---|---|
| `while not state.is_terminal()` | 条件边回路 + 终止状态守卫（非 RUNNING → END） | `runtime.py` ↔ `graph.py` |
| 循环顶部 `iteration += 1` + `decide_next()` | `decide` 节点：递增 iteration + 调 `model.decide_next(StateProxy(state))` | `runtime.py:34-38` ↔ `nodes.py` |
| 循环顶部 `iteration >= max_iterations` 检查 | `route_decide_or_max` 条件边（确定性，先于 decide 执行）→ `max_iterations` 节点 | `runtime.py:33` ↔ `routing.py` |
| `decide_next()` 的业务决策 if/elif | `decide` 节点的模型调用；`route_by_next_action` 只按 `next_action` 分发 | `models.py` ↔ `routing.py` |
| `generate_sql()` / `fix_sql()` / `validate()` / `execute()` 函数调用 | Node（`generate_sql` / `fix_sql` / `finalize`） | `runtime.py` ↔ `nodes.py` |
| `state.apply_candidate/apply_validation/apply_execution` 显式更新 | 节点返回部分 State 更新，channel 合并 | `state.py` ↔ `state.py` |
| `state.record_round()` 追加 history | reducer（`Annotated[list[StepEvent], operator.add]`） | `state.py` ↔ `state.py` |
| `state.fail()` / `complete_success()` / `exceed_max_iterations()` | 节点写 `status` / `failure_reason` / `final_answer` | `state.py` ↔ `nodes.py` |
| `is_terminal()` 三种终止 | `finalize → END`（SUCCESS / FAILED）、`max_iterations → END`、终止状态守卫 | `state.py` ↔ `graph.py` |
| `try/except` 包住整轮调度 | 节点级 `_failure_boundary` 异常转换（保留状态）；Graph Runtime 异常由 `agent.py` 兜底 | `runtime.py` ↔ `nodes.py` + `agent.py` |

## 2. 两份代码的执行流程

**手写**：`Agent.invoke` → 构造 AgentState → `while` 循环逐轮：迭代检查 → `decide_next` → `_dispatch`（调用函数 + 更新 State）→ `record_round` → 循环条件。

**Graph**：`LangGraphAgent.invoke` → 构造完整初始 State → `graph.invoke(initial)` → LangGraph 运行时从 START 出发：`route_decide_or_max`（确定性检查）→ `decide`（递增 iteration + `model.decide_next`）→ `route_by_next_action`（按 next_action 分发）→ 动作节点（generate / fix / finalize）→ 回到确定性检查（循环回路）→ END。

两者轮次完全一致：decide+generate（第 1 轮）→ decide+fix（第 2 轮）→ decide+finalize（第 3 轮），`iteration` 数值相同。

## 3. 控制权在哪里

- **手写**：控制流在开发者写的 `while` / `if/elif` 代码里，运行时就是这段代码本身。
- **Graph**：控制流在**图声明**里（节点 + 边 + 条件边），LangGraph 运行时负责执行图；路由函数只做两类事：确定性的上限检查（`route_decide_or_max`）与按模型决策分发（`route_by_next_action`）。

两种形态下，**业务动作决策都只发生在模型身上**（手写：`decide_next`；Graph：`decide` 节点调用同一个 `decide_next`）——路由/图结构不替代模型做业务决策，迭代与终止由确定性机制保证。这与第 0 章 0.5 的结论一致。

## 4. State 如何更新

- **手写**：可变 dataclass，Runtime 显式调用 `apply_*` 方法。
- **Graph**：TypedDict，节点返回「部分更新」字典，LangGraph 按 channel 合并；`history` 用 reducer 追加。

教学点：Graph 的更新规则是**声明式**的（channel 语义 + reducer），不再散落在调用代码里。

## 5. Loop 如何表示

- **手写**：`while` 循环 + 循环内的分支。
- **Graph**：动作节点（generate / fix）→ `route_decide_or_max` → `decide` → `route_by_next_action` → 动作节点的**条件边回路**——回到 decide 意味着进入下一轮，这就是循环的图表示。终止由两种方式保证：终止状态守卫（非 RUNNING → END）与 `max_iterations` 节点。

## 6. 终止如何表示

- **手写**：`is_terminal()`（SUCCESS / FAILED / MAX_ITERATIONS_REACHED）+ 循环退出。
- **Graph**：终止节点连 `END` 边；「已经 SUCCESS 后继续执行」在图中不可能发生——没有出边。

## 7. 错误处理如何表示

- **手写**：`try/except` 包住整轮调度，任何异常 → `FAILED + failure_reason`，异常发生轮的 iteration / history 保留。
- **Graph**：两层边界——① **节点级异常转换（主要机制）**：generate / fix / finalize / decide 统一由 `_failure_boundary` 包裹，模型 / 工具非预期异常转为 State 更新（FAILED + failure_reason + 正确 iteration + 失败 history 事件），异常前状态由 channel 合并自动保留，**与手写语义一致**；② **Graph Runtime 级异常（兜底）**：路由函数异常、LangGraph 内部错误由 `invoke` 层捕获转 FAILED——无 Checkpointer 时不保留部分执行状态，这是明确的教学边界，也是 Checkpoint 能力（v0.6.0）的教学伏笔。

可预期的工具失败（Executor 返回失败）在两种实现中都走普通 State 更新路径，不抛异常。

## 8. 测试如何证明行为等价

`tests/basic_langgraph/test_langgraph_agent.py` 的 `test_direct_equivalence_with_manual` 对同一输入断言：status、current_sql、execution_result.data、final_answer、iteration、history 动作序列逐项相等；另有 off-by-one（max_iterations=2 时 finalize 不得执行）、无跨 invoke 污染、reducer 无重复追加等专项测试。

## 9. 当前未使用的 LangGraph 能力

Checkpoint / Checkpointer、Interrupt（HITL）、Streaming（astream）、Send / Command、Subgraph、RetryPolicy / fallback、RecursionLimit 调整——均属于 v0.4.0 ~ v0.6.0 里程碑，本对照刻意不使用，以保持「行为等价迁移」的纯粹性。
