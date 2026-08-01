# LLM vs Runtime（本项目最重要的边界）

## 核心命题：LLM 不是 Runtime

第 0 章 0.2 的判据：控制流在谁手里。模型负责 **Decision**——决定下一步做什么、生成什么内容；Runtime 负责 **Control**——循环、轮次、分发、终止、失败处理。

| 维度 | LLM（模型） | Runtime |
|---|---|---|
| 职责 | Decision：`decide_next()` / `generate_sql()` / `fix_sql()` | Control：Loop / Dispatch / Iteration / Retry / Error Boundary / 终止 |
| 载体 | `examples/manual_agent_loop/models.py`（`FakeLLM`） | `runtime.py` / `graph.py` + `nodes.py` + `routing.py` |
| 确定性承诺 | 无 | `max_iterations` 兜底、终止状态守卫（ADR-004：代码保证） |
| 可替换性 | 同一 `FakeLLM` 被两个 Runtime 复用 | while → LangGraph（TASK-0003）→ 未来 Temporal / Durable Execution / Workflow Engine |

这条边界不是理论，是 PR #4 Review Blocker 1 的 enforcement 结果：basic_langgraph 第一版让路由函数根据校验结果决定 generate / fix / finalize（模型没有参与决策），Review 判定为不等价。修复后 `decide` 节点调用 `model.decide_next()`，路由函数只做确定性检查与按 `next_action` 分发。

## 证据链：Runtime 演进而 Agent 不变

```text
Manual Runtime（while，runtime.py）
    ↓ TASK-0003：行为等价迁移（同一 FakeLLM / Validator / Executor 复用）
LangGraph Runtime（条件边回路，graph.py）
    ↓ 未来（待验证，ADR-003：框架不绑定）
Temporal / Durable Execution / Workflow Engine
```

每一次切换，同一个 `FakeLLM`、同一个 `FakeSQLValidator` / `FakeSQLExecutor`、同一组行为断言（`test_direct_equivalence_with_manual`）保持成立——**Agent 的定义（第 0 章 0.3 五要素）不依赖 Runtime 载体**。

## Framework 没有创造 Agent，只是改变 Runtime

第 0 章 0.7：从手写到框架是「表示迁移，不是能力获得」。事实链：

- PR #2 的手写 Demo 已经是 Agent（五要素齐全：目标 / 决策 / 能力 / 状态 / 结果）
- TASK-0003 引入 LangGraph **没有新增任何 Agent 能力**（明确禁止 Checkpoint / Memory / HITL / Streaming），只是改变了循环的载体
- 两个版本输出逐行一致（`main.py` 对照）

推论（写代码与 Review 时必须遵守）：

1. 引入框架 ≠ 引入 Agent 能力；框架不能替代业务规则（ADR-004 / ADR-005、`AGENTS.md` 安全底线）
2. 模型决策必须显式属于模型——路由 / 业务代码不得替代 `decide_next`（PR #4 Review Blocker 1）
3. Runtime 差异不得改变业务语义——行为等价必须有对照测试证明（PR #4 Review Focus）
