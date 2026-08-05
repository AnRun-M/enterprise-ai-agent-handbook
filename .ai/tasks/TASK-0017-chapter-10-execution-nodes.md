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
- **Node 是 Graph Runtime 管理的执行单元**：实现上可为普通 Python callable，但语义上是执行单元（读 State、执行能力、返回部分更新、进入运行时调度与错误边界）；不是孤立函数、不是 Tool、不是调度器
- **节点不调用下一个节点、不写 while**：调度权在路由 / Graph Runtime（ch11）；循环属于 Runtime（ch01）
- **compile / invoke 不提前展开**：属 Graph Runtime 执行路径（ch11 引出），本章仅引用 `agent.py` invoke 作为入口
- **不提前讲**：Reducer（ch12）/ Edge & Conditional Edge（ch11）/ Checkpoint（ch14）/ Interrupt（ch15）/ Streaming（ch16）/ Subgraph（ch17）
- **LangChain 仅允许一句边界**：Node 可以包装 Runnable；create_agent 底层使用 LangGraph Runtime——不介绍 Runnable API / LCEL / create_agent / Messages / PromptTemplate / Middleware，全部留给 Future LangChain Scope Planning
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
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
