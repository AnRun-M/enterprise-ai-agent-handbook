# State Design Principles

## State 是 Runtime 的唯一事实来源

两个实现的等价测试 `test_direct_equivalence_with_manual` 断言的就是 State 字段：status / current_sql / execution_result / final_answer / iteration / history 动作序列——**行为等价 = State 等价**。

TASK-0003 要求 `GraphState` 与 `AgentState` 字段语义对齐（11 个字段一一对应）。跨轮次的全部信息都在 State 里：

- 无全局变量（TASK-0002 测试 `test_state_is_pure_dataclass_no_globals`）
- 无聊天上下文依赖（ADR-006 的原则推广：跨轮次信息如果不在显式载体里，就无法被程序校验、审计与测试）

## 每个字段为什么存在

| 字段 | 为什么必须存在 |
|---|---|
| `user_question` | 目标是 Agent 的输入定义（第 0 章 0.3 五要素） |
| `current_sql` | 模型动作的产物，是校验（T05）、修复（T07）、执行（T09）的输入 |
| `validation_error` / `validation_rule` | 校验结果双通道：错误消息给展示与审计，**规则名给修复决策**。PR #2 实现中曾只存消息，导致 `FakeLLM.fix_sql` 的修复分支永不命中（`state.validation_error` 是消息文本、`state.validation_rule` 才是 "missing_limit"）——教训：**决策需要什么信息，State 就必须显式存什么** |
| `execution_result` | 工具输出（T09），是 T12 最终回答的输入 |
| `final_answer` | 最终结果（T12 结构化输出） |
| `failure_reason` | PR #2 Review Blocker 1：失败后调用方必须能在最终 State 回答"为什么失败"，而不是去翻异常栈或日志 |
| `iteration` | PR #4 Review Blocker：off-by-one 是行为等价的一部分，必须可断言 |
| `status` | 生命周期（SUCCESS / FAILED / MAX_ITERATIONS_REACHED） |
| `history` | 可观测与测试断言（每轮：iteration / action / status / sql / validation_error / note） |

## 为什么 State 不能依赖聊天上下文

1. **上下文不可测试**：测试无法断言"模型上一轮记住了什么"。State 可以——断言 `state["history"][0].validation_error == "missing LIMIT clause"`。
2. **上下文不可恢复**：进程崩溃后模型上下文即丢失。两个 Runtime 都没有 Checkpointer 时，State 是唯一可延续的信息（TASK-0002 / TASK-0003 的共同事实）。
3. **ADR-006 的原则推广**：Agent 内部与仓库协作一样——记忆必须落在显式载体里，不依赖不可控的"记忆"。

## 为什么 State 比 Prompt 更重要

ADR-005：Prompt 不承担全部业务规则，规则按层拆分。State 是其中"程序化校验"与"会话上下文"层的载体：

- 校验结果（`validation_error` / `validation_rule`）来自程序（T05 静态校验），不是来自模型输出
- `iteration` / `status` 由代码保证（ADR-004）
- Prompt 只决定模型产出的内容（SQL 文本）

证据：修复循环的工作机制是"State 里的 `validation_rule` 驱动 `FakeLLM.fix_sql`"——模型**读 State 修复**，而不是凭模型记忆修复。State 是事实，Prompt 是输入约束。

## 为什么 failure_reason 必须进入 State

PR #2 Review Blocker 1 的验收：三种失败场景（Executor 失败 / 模型或工具异常 / 未知 Action）都能在最终 State 获得明确原因。原因：

- 调用方（`main.py`、上层服务）只持有最终 State——失败原因不在 State，就在不可达的地方
- 审计与排障需要统一读取点：`state.failure_reason` 与 `state.history` 中的失败事件
- `test_execution_failure_saves_failure_reason` / `test_runtime_exception_saves_failure_reason` / `test_unknown_action_saves_failure_reason` 是这条规则的测试固化
