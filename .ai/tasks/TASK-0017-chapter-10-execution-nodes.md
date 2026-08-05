# TASK-0017：Chapter 10《Execution Nodes——Node 执行模型》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 |
| Related Chapter | 第 1 章（Loop）、第 5 章（Tool Registry）、第 6 章（Scheduler）、第 9 章（Graph State）、第 8 章（为什么是图）；TASK-0014（Part 03 规划） |
| Related Example | examples/basic_langgraph（nodes.py / graph.py / agent.py / routing.py / state.py） |
| Related Test | tests/basic_langgraph（`test_model_exception_saves_failure_reason` / `test_fix_exception_preserves_state_and_history` / `test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 第二个原语章 `docs/03-langgraph-core/ch10-execution-nodes.md`：回答「手写 Runtime 的动作分支如何在图中成为执行单元？」。**Node 作为 Graph Runtime 管理的执行单元（Execution Unit）展开，而不是普通 Python 函数教程**——读取 State → 执行能力 → 返回 Partial State Update → Graph Runtime 合并 → 进入下一执行步骤；Node 不等于 Tool、不等于 Python function、不等于 Runnable。

## 需要新增

- `docs/03-langgraph-core/ch10-execution-nodes.md`（10.1-10.12 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0017-chapter-10-execution-nodes.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 10 章）
- `docs/03-langgraph-core/index.md`（第 10 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 10 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 10 条目，draft / 待架构审查）
- `.ai/context/current.md`（含 Future LangChain Scope Planning 补全——已并入既有条目，不新增第二份）

## 约束

- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch01 Loop / ch05 Tool Registry / ch06 Scheduler / ch09 Graph State），再讲 LangGraph 承载；禁止从 API 出发解释概念
- **Node 是 Graph Runtime 管理的执行单元**：实现上可为普通 Python callable，但语义上是执行单元（读 State、执行能力、返回更新、进入运行时调度与错误边界）；不是孤立函数、不是 Tool、不是调度器
- **执行与路由两层表述**：当前 Demo 将执行与路由严格拆开（Node 返回 State Update、Conditional Edge 决定下一步，便于独立测试）；**这不是 LangGraph 对所有 Node 的强制限制**——Node 通过 Command 携带 State Update 与路由意图的机制留第 13 章，跳转解释权仍在 Graph Runtime
- **Graph Runtime / 应用职责拆分**：Graph Runtime 负责调度调用 / 提供输入 / 接收结果 / 合并 / 继续执行 / 传播异常；应用负责定义 Node callable / 契约 / 依赖注入 / 业务错误转换（`_failure_boundary` 是应用实现，非 LangGraph 自动 FAILED 机制）
- **Failure Boundary 两层分叉**：节点级捕获 → FAILED State Update → 正常合并；未捕获 / 路由 / 框架异常 → invoke 外层兜底；两层不是同一异常连续执行两次；异常前状态保留是有条件的（未被 Update 覆盖的 channel 保留已有值，非事务回滚，测试仅覆盖具体场景）
- **节点分类四类形态**：Semantic Decision（decide）/ Mixed Capability（generate / fix）/ External Execution（finalize）/ Deterministic Compute（max_iterations）
- **Tool Registry 证据边界**：能力经 Node Factory 依赖注入；basic_langgraph 尚未实现 Tool Registry lookup；Validator / Executor 不得写成"经 Registry 注册并分发"；ch05 Registry 是未来可替换的能力组织方式（Dispatcher 不展开）
- **Node 输入来源**：跨轮次控制事实从 Graph State 读取；能力经 Node Factory 显式注入；Runtime Context 等请求级依赖显式传入；禁止未声明的模块级可变状态 / 隐藏缓存 / 隐式跨轮记忆；Node dependency 不是 State 字段
- **State Update 范围**：只在"当前 Demo 的图执行阶段"由 Node 返回的 Update 发起、Graph Runtime 按 channel 合并；不覆盖 Initial State 构造 / Reducer / Command / Checkpoint / resume
- **Node 输出为当前 Demo 形态**："优先只返回实际变化字段"是工程建议（减少覆盖风险、意图清晰），不是框架绝对禁令
- **compile / invoke 不提前展开**：属 Graph Runtime 执行路径（ch11 引出），本章仅引用 `agent.py` invoke 作为入口
- **不提前讲**：Reducer（ch12）/ Edge & Conditional Edge（ch11）/ Command（ch13）/ Checkpoint（ch14）/ Interrupt（ch15）/ Streaming（ch16）/ Subgraph（ch17）
- **LangChain 仅一句边界**：Node 的实现可以包装兼容的 callable / Runnable——不出现 Runnable API / LCEL / create_agent / AgentExecutor / Messages / PromptTemplate / Middleware，全部留给 Future LangChain Scope Planning
- **Tool Registry / Scheduler / State / Context 只引用不重新定义**（ch05 / ch06 / ch02 / ch03）
- 证据诚实：节点测试断言行为契约与错误转换；"所有 Node 输入不可变性"无统一测试，如实标注；测试数量以最新 CI 为准不写死
- 不修改已完成章节、principles、ADR、依赖、Part 03 冻结章节顺序；ROADMAP 仅加 draft 行、content-map 仅加第 10 章行

## 验收标准

- [ ] 章节结构 10.1-10.12 完成，Q1-Q10 全部回答
- [ ] 主线明确：Node 是 Graph Runtime 管理的执行单元（实现可为 callable，语义非孤立函数）
- [ ] 每节先 Runtime 语义后 LangGraph 承载，无 API 先行的解释
- [ ] 5 张 Mermaid 图（手写分支→节点映射 / 执行单元循环 / 三类节点分类 / Failure Boundary 两层 / Node≠Tool 边界）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0017 Status = in_progress；ROADMAP Chapter 10 = draft / 待架构审查；content-map 第 10 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-10-execution-nodes，commit `docs: draft chapter 10 execution nodes`）
- [ ] PR #31 Architecture Review 九项修正全部应用（Node/Routing 通用边界两层 / Graph Runtime 与应用职责 / Failure Boundary 控制流分叉 / Node 输出契约 / 四类节点分类 / Tool Registry 证据边界 / Node 输入来源 / State Update 范围 / 异常前状态保留条件 / LangChain API 清理）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #31 创建。
- 2026-08-05：**PR #31 Architecture Review 九项修正**（commit：docs: refine node execution and runtime boundaries）全部应用并推送更新 PR #31：
  1. **Node / Routing 通用边界两层**：当前 Demo 执行与路由严格拆开（Node 返回 State Update、Conditional Edge 决定下一步）是设计选择非框架强制；Command 携带路由意图留第 13 章——主线 / 10.2 / 10.5 / 10.8 / 误区 #2 / Q2 / Q8
  2. **Graph Runtime / 应用职责拆分**：Runtime 负责调度 / 输入 / 接收结果 / 合并 / 控制流 / 异常传播；应用负责 Node 定义 / 契约 / 注入 / 业务错误转换；`_failure_boundary` 是应用实现非框架自动机制——10.2 / 对照表 / 10.7 / 10.8 / Q2 / Q6
  3. **Failure Boundary 控制流分叉**：节点级捕获 → FAILED Update → 正常合并；未捕获 / 路由 / 框架异常 → invoke 外层兜底；两层不是同一异常执行两次；Mermaid 重画
  4. **Node 输出契约收窄**：`Callable[[GraphState], dict]` 为当前 Demo 形态；通用层 Node 返回 Runtime 可解释的更新或控制结果（Command 属 ch13）；"只返回实际变化字段"改为工程建议非绝对禁令
  5. **节点分类修正为四类形态**：Semantic Decision / Mixed Capability / External Execution / Deterministic Compute（替代 LLM/Tool/Pure Compute 三分类）
  6. **Tool Registry 证据边界**：能力经 Node Factory 依赖注入；Demo 未实现 Tool Registry lookup；Validator / Executor 不得写成经 Registry 注册分发；ch05 Registry 为未来组织方式
  7. **Node 输入来源修正**：Graph State 读控制事实 + 能力显式注入 + 请求级依赖显式传入；禁止未声明模块级可变状态 / 隐藏缓存 / 隐式跨轮记忆；Node dependency 不是 State 字段
  8. **State Update 范围收窄**：仅"当前 Demo 图执行阶段"由 Node 返回 Update 发起、Runtime 按 channel 合并；不覆盖 Initial State / Reducer / Command / Checkpoint / resume
  9. **异常前状态保留条件化**：未被 Update 覆盖的 channel 保留已有值；非事务回滚；前提 Node 未原地修改可变对象；测试仅覆盖具体场景
  10. **LangChain API 清理**：删除"create_agent 底层使用 LangGraph Runtime"；仅保留"Node 可以包装兼容 callable / Runnable"一句；正文不再出现 create_agent / AgentExecutor / PromptTemplate / Messages / Middleware
