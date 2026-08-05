# TASK-0018：Chapter 11《Edge 与 Conditional Edge——静态边与条件路由》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | 第 1 章（Loop / 终止）、第 6 章（Scheduler：Routing + Lifecycle Guard）、第 9 章（Graph State：START/END）、第 10 章（Execution Nodes）；TASK-0014（Part 03 规划） |
| Related Example | examples/basic_langgraph（graph.py / routing.py / nodes.py / agent.py） |
| Related Test | tests/basic_langgraph（`test_router_*_is_pure` / `test_max_iterations_2_stops_before_finalize` / `test_model_decision_*_is_routed` / `test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 第三个原语章 `docs/03-langgraph-core/ch11-edge-conditional-edge.md`：回答「Graph Runtime 如何根据执行结果连接节点并选择下一执行步骤？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Edge 描述确定性连接；Conditional Edge 根据运行时结果选择后续路径；路由函数产生 Route Decision；Graph Runtime 解释该结果并调度下一执行步骤。当前 Demo 将模型语义决策写入 State，再由确定性路由函数分发，避免路由层替代模型决策。

## 需要新增

- `docs/03-langgraph-core/ch11-edge-conditional-edge.md`（11.1-11.11 结构，回答 Q1-Q10，6 张 Mermaid 图）
- `.ai/tasks/TASK-0018-chapter-11-edge-conditional-edge.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 11 章）
- `docs/03-langgraph-core/index.md`（第 11 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 11 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 11 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch01 Loop / ch06 Routing + Lifecycle Guard / ch09 START-END / ch10 Node），再讲 LangGraph 承载；禁止从 API 出发解释概念
- **Edge 是连接描述，不是执行者**：不调用节点、不做业务判断；执行节点与解释路径的是 Graph Runtime
- **Conditional Edge 是运行时路径选择机制，不等于模型决策**：不得写"Conditional Edge 自己调用节点"
- **Route Decision ≠ Scheduling Execution**：路由函数产生 route result（纯函数化是工程选择非框架强制）；Graph Runtime 负责解释与调度
- **模型语义决策在 decide 节点发生**：route_by_next_action 只按 State 中 next_action 分发，不重新判断业务意图、不调用 LLM、不重写 next_action；未知值以实际代码为准（RuntimeError → invoke 兜底）
- **route_decide_or_max 按真实代码讲**（终止守卫最先 → iteration >= max → max_iterations；否则 → decide）；定位为 Lifecycle Guard + 确定性路由，不是语义动作决策器；上限检查先于模型动作；off-by-one 语义
- **END 是执行终点 ≠ 业务成功**；FAILED / MAX_ITERATIONS_REACHED 也进 END；Human Stop / Interrupt 是暂停不能画成 END（API 留第 15 章）
- **不提前展开**：Reducer（ch12）/ Command / Send（ch13）/ Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17）
- **不引入 LangChain API**；不重新定义 Runtime Scheduler（ch06 唯一事实源）
- 证据以仓库真实代码与测试为准（routing.py / graph.py / tests）；与任务书建议不一致处以代码为准并报告差异（例：START 出口为条件边而非静态边）
- 测试数量以最新 CI 为准不写死；未验证清单如实标注
- 不修改 TASK-0014、Chapter 08/09/10、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope 内容、Part 编号

## 验收标准

- [ ] 章节结构 11.1-11.11 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持
- [ ] 6 张 Mermaid 图（Node+Edge 控制流 / Edge vs Conditional Edge / decide→State next_action→路由分发 / route_decide_or_max 守卫顺序 / Route Decision→Graph Runtime→Next Node / START-END 与业务状态关系）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0018 Status = in_progress；ROADMAP Chapter 11 = draft / 待架构审查；content-map 第 11 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-11-edge-conditional-edge，commit `docs: draft chapter 11 edge and conditional edge`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
