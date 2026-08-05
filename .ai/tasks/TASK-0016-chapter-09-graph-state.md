# TASK-0016：Chapter 09《Graph State——状态如何进入图》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | 第 2 章（Execution State）、第 3 章（Model Context）、第 7 章（Memory）、第 8 章（为什么是图）；TASK-0014（Part 03 规划） |
| Related Example | examples/basic_langgraph（state.py / graph.py / nodes.py / agent.py / routing.py）、examples/manual_agent_loop |
| Related Test | tests/basic_langgraph（`test_initial_state_complete` / `test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 第一个原语章 `docs/03-langgraph-core/ch09-graph-state.md`：回答「**Execution State 如何被 LangGraph 的 Graph State 承载？**」。核心主线：Execution State 是 Runtime 语义；Graph State 是 LangGraph 对该状态契约的承载方式。State schema 定义图中有哪些状态字段、节点可读取什么、可返回什么更新、哪些字段需要 reducer、初始 State 如何进入图；不重新定义 State 业务边界 / Memory / Context / Checkpoint / Tool Registry / Policy。

## 需要新增

- `docs/03-langgraph-core/ch09-graph-state.md`（9.1-9.11 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0016-chapter-09-graph-state.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 9 章）
- `docs/03-langgraph-core/index.md`（第 9 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 9 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 09 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **Runtime 第一视角、Framework 第二视角**：先引用第 2 章 Execution State 语义（只引用不重新定义），再讲 LangGraph 承载；禁止从 API 出发解释概念
- **TypedDict 是当前 Demo 选择，不是唯一方案**：State schema 不限定必须是 TypedDict，不写死框架强制
- **START / END 是图结构哨兵，不是业务 State 字段**：END ≠ 业务成功；Human Stop / Interrupt 是暂停态，不等同 END（不提前展开 Interrupt API）
- **Node 返回部分更新**，不要求返回完整 State；Reducer 只作为挂载点提及，机制留第 12 章
- 不展开 Checkpoint / Interrupt / Stream 机制（只立边界，标注第 14 / 15 / 16 章）
- compile / invoke 的图执行机制属 Graph Runtime，本章仅最小用法（初始 State 进入图的路径）
- 不新增 LangChain 内容
- 证据诚实：只写仓库真实验证的结论；不写"完整逐轮 State Snapshot 等价 / Checkpoint recovery 已验证 / 并发合并已验证 / Send / Command 已验证 / 一般性 Graph State 可替换已证明"
- 测试数量以最新 CI 为准，不写死
- 不修改 TASK-0014、Chapter 08 正文、examples、tests、principles、ADR、依赖、Part 03 冻结章节顺序

## 验收标准

- [ ] 章节结构 9.1-9.11 完成，Q1-Q10 全部回答
- [ ] 主线明确：Execution State 是 Runtime 语义；Graph State 是 LangGraph 承载；schema 是数据契约不是业务规则引擎
- [ ] 每节先 Runtime 语义后 LangGraph 承载，无 API 先行的解释
- [ ] 5 张 Mermaid 图（Execution State → Graph State 承载 / Schema 定义与非定义 / Initial State → START → Execution → END / Node 读取与部分更新 / Graph State 与 Context-Memory-Checkpoint 边界）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0016 Status = in_progress；ROADMAP Chapter 09 = draft / 待架构审查；content-map 第 9 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-09-graph-state，commit `docs: draft chapter 09 graph state`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
