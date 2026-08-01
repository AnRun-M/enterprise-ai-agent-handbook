# Testing Agent

## 为什么不能只测 Prompt

Prompt 是单次模型调用的输入约束（`TERMINOLOGY.md`）。ADR-005 的理由：规则塞进 Prompt 的后果是"不可测试、不可审计"。Agent 的行为是多轮交互的结果——只验证 Prompt 内容无法回答三个问题：

- "校验失败后是否进入了修复循环？"→ 断言 `history[1].action is ActionType.FIX_SQL`
- "达到上限是否安全终止？"→ 断言 `status is MAX_ITERATIONS_REACHED`
- "失败原因是否保存了？"→ 断言 `failure_reason`

本项目全部行为断言都是 **State Transition 断言**：invoke 之后检查最终 State（status / iteration / history / failure_reason / current_sql……），而不是断言"模型收到了什么 Prompt"。

## 为什么 FakeLLM 价值巨大

1. **确定性**：`FakeLLM` 行为脚本化（首轮生成缺 LIMIT 的 SQL → 二轮按 `validation_rule` 修复），同一输入永远同一输出——测试完全可复现（TASK-0002 的硬性要求）。
2. **可注入**：依赖注入（`AGENTS.md` 代码规范）让测试能替换任意组件：`ExplodingModel`（模型抛异常）、`AlwaysRejectValidator`（永远校验失败）、`FailingExecutor`（执行失败）——两个 Runtime 的错误路径全部可测，且异常路径的测试 Fake 与正常路径共用同一个 `Agent` 构造接口。
3. **可对照**：两个 Runtime 共享同一 `FakeLLM`（TASK-0003 复用），等价测试 `test_direct_equivalence_with_manual` 才可能成立——同一输入下两个实现的 State 逐字段相等。

## 为什么 Deterministic 才能持续 CI

`tests.yml`（CI 门禁，TASK-0002 引入）在每次 push / PR 时运行 pytest。持续集成的先决条件是"同样的代码永远同样的结果"：

- 真实 LLM 输出不可复现 → 测试 flaky → CI 失去信号价值，红灯无法归因
- `langgraph==1.2.9` 精确固定（`pyproject.toml`，TASK-0003）→ 依赖版本不漂移
- 全仓 pytest：`tests/manual_agent_loop`（31）+ `tests/basic_langgraph`（26）= **57 passed**，全部无网络、无真实数据库、无 API Key

## 测试层次（本项目已验证的结构）

1. **组件规则测试**：`test_validator.py`（12 个，含参数化拒绝用例——SELECT 首 token 严格匹配）
2. **Loop 行为测试**：`test_agent_loop.py`（状态迁移 / 三种终止 / history 事件序列 / failure_reason 三场景）
3. **Graph 行为测试**：`test_langgraph_agent.py`（路由纯函数 / reducer 无重复 / 异常保状态 / 决策路由）
4. **等价对照测试**：`test_direct_equivalence_with_manual`（两个 Runtime 同一断言集）
5. **卫生测试**：`test_no_cross_invoke_pollution`（无跨请求状态污染）
