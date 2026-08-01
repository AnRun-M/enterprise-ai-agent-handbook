# 手写 Runtime vs LangGraph：一一对照

> 本文是 Part 3 的对照速览，不是完整教程。完整章节在 v0.4.0 里程碑展开。
> 对应实现：`examples/manual_agent_loop/`（手写）与 `examples/basic_langgraph/`（Graph）。
> 行为等价由 `tests/basic_langgraph/test_langgraph_agent.py` 证明。

## 1. 逐项映射表

| 手写 Runtime（manual_agent_loop） | LangGraph（basic_langgraph） | 文件 |
|---|---|---|
| `while not state.is_terminal()` | 条件边回路 + `END` 终止 | `runtime.py` ↔ `graph.py` |
| 循环顶部 `iteration >= max_iterations` 检查 | 路由函数中的上限优先判断 → `max_iterations` 节点 | `runtime.py:33` ↔ `routing.py` |
| `decide_next()` 的 if/elif | `route_after_model_action` 条件边（纯函数） | `models.py` ↔ `routing.py` |
| `generate_sql()` / `fix_sql()` / `validate()` / `execute()` 函数调用 | Node（`generate_sql` / `fix_sql` / `finalize`） | `runtime.py` ↔ `nodes.py` |
| `state.apply_candidate/apply_validation/apply_execution` 显式更新 | 节点返回部分 State 更新，channel 合并 | `state.py` ↔ `state.py` |
| `state.record_round()` 追加 history | reducer（`Annotated[list[StepEvent], operator.add]`） | `state.py` ↔ `state.py` |
| `state.fail()` / `complete_success()` / `exceed_max_iterations()` | 节点写 `status` / `failure_reason` / `final_answer` | `state.py` ↔ `nodes.py` |
| `is_terminal()` 三种终止 | `finalize → END`（SUCCESS / FAILED）、`max_iterations → END` | `state.py` ↔ `graph.py` |
| `try/except` 包住整轮调度 | 节点内可预期失败转 State；非预期异常由 `agent.py` 层捕获转 FAILED | `runtime.py` ↔ `agent.py` |

## 2. 两份代码的执行流程

**手写**：`Agent.invoke` → 构造 AgentState → `while` 循环逐轮：迭代检查 → `decide_next` → `_dispatch`（调用函数 + 更新 State）→ `record_round` → 循环条件。

**Graph**：`LangGraphAgent.invoke` → 构造完整初始 State → `graph.invoke(initial)` → LangGraph 运行时从 START 出发：`generate_sql` 节点 → 条件边 →（`fix_sql` 回路 / `finalize` / `max_iterations`）→ END。

两者轮次完全一致：generate（第 1 轮）→ fix（第 2 轮）→ finalize（第 3 轮），`iteration` 数值相同。

## 3. 控制权在哪里

- **手写**：控制流在开发者写的 `while` / `if/elif` 代码里，运行时就是这段代码本身。
- **Graph**：控制流在**图声明**里（节点 + 边 + 条件边），LangGraph 运行时负责执行图；路由函数是唯一决定「下一步去哪」的地方。

两种形态下，**模型都只做决策的一部分**（生成 SQL / 修复 SQL），迭代与终止由确定性机制保证——这与第 0 章 0.5 的结论一致。

## 4. State 如何更新

- **手写**：可变 dataclass，Runtime 显式调用 `apply_*` 方法。
- **Graph**：TypedDict，节点返回「部分更新」字典，LangGraph 按 channel 合并；`history` 用 reducer 追加。

教学点：Graph 的更新规则是**声明式**的（channel 语义 + reducer），不再散落在调用代码里。

## 5. Loop 如何表示

- **手写**：`while` 循环 + 循环内的分支。
- **Graph**：`generate_sql` / `fix_sql` 之间的**条件边回路**——从 `fix_sql` 可以回到条件边再次路由，这就是循环的图表示。

## 6. 终止如何表示

- **手写**：`is_terminal()`（SUCCESS / FAILED / MAX_ITERATIONS_REACHED）+ 循环退出。
- **Graph**：终止节点连 `END` 边；「已经 SUCCESS 后继续执行」在图中不可能发生——没有出边。

## 7. 错误处理如何表示

- **手写**：`try/except` 包住整轮调度，任何异常 → `FAILED + failure_reason`。
- **Graph**：三层边界——① 节点内可预期失败转 State（finalize 处理 Executor 失败）；② 非预期异常不在节点内捕获，由 LangGraph 抛出；③ `invoke` 层捕获转 `FAILED + failure_reason`。

差异说明：Graph 版异常时不保留部分执行状态（无 Checkpointer），这是明确的边界，也是 Checkpoint 能力（v0.6.0）的教学伏笔。

## 8. 测试如何证明行为等价

`tests/basic_langgraph/test_langgraph_agent.py` 的 `test_direct_equivalence_with_manual` 对同一输入断言：status、current_sql、execution_result.data、final_answer、iteration、history 动作序列逐项相等；另有 off-by-one（max_iterations=2 时 finalize 不得执行）、无跨 invoke 污染、reducer 无重复追加等专项测试。

## 9. 当前未使用的 LangGraph 能力

Checkpoint / Checkpointer、Interrupt（HITL）、Streaming（astream）、Send / Command、Subgraph、RetryPolicy / fallback、RecursionLimit 调整——均属于 v0.4.0 ~ v0.6.0 里程碑，本对照刻意不使用，以保持「行为等价迁移」的纯粹性。
