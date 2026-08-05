# TASK-0018：Chapter 11《Edge 与 Conditional Edge——静态边与条件路由》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
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
- **三层职责（Edge/Scheduler 关系）**：Edge / Conditional Edge declaration 描述固定连接或路由挂载关系（不执行 Node）→ Routing callable 产生路径结果（也不执行 Node）→ Graph Runtime / Scheduling Execution 解释路径结果并调度下一 Node；**"Edge 是 Runtime 控制流的声明载体，不是 Scheduler 本身"**
- **普通静态 Edge 是构建期声明的固定连接，不读取 State，也不执行运行时判断**；读取 State 的是与 Conditional Edge 关联的 routing callable（在运行时被调用）
- **Conditional Edge 两层定义**：概念层 = 关联 routing callable，返回 Graph Runtime 可解释的路径结果；当前 Demo = 符号化 route key + path map（`_DECIDE_OR_MAX_MAP` / `_BY_ACTION_MAP`）映射节点——**path map 是当前 Demo 的接线方式，不是所有 Conditional Edge 的必经结构**（不展开其他 API 形式）
- **Route Decision 三层**：定义 = 根据 State 与显式 runtime facts 产生路径结果；工程推荐 = 尽量确定性 / 无副作用 / 可独立测试 / 依赖显式化；当前 Demo 事实 = 两个路由函数被实现并测试为纯函数——**"纯函数化"不是 Route Decision 的定义组成部分**
- **next_action 写入 State 是当前 Demo 的显式契约设计，非框架强制**（收益：解耦 / 独立测试路由 / 双 Runtime 对照 / 为 Trace-审计提供可记录依据——不是"写进 State 就等于已实现审计"）；Command 等其他控制结果表达方式留第 13 章；不得写"所有模型决策都必须进入普通 State 字段"或"Conditional Edge 必须从 next_action 字段路由"
- **Routing error 归属**：route_by_next_action 是应用定义的 routing callable，非法 next_action 是应用路由契约错误——异常由应用 callable 产生、Graph Runtime 调用与传播、应用级 invoke 外层兜底构造 FAILED State；**不是 LangGraph 自动业务错误转换，不称其为 LangGraph 内部错误**
- **模型语义决策在 decide 节点发生**：route_by_next_action 只按 State 中 next_action 分发，不重新判断业务意图、不调用 LLM、不重写 next_action
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
- [x] PR #33 Architecture Review 六项修正全部应用（Routing error 归属 / Conditional Edge 两层定义 / next_action 作用域 / Route Decision 三层 / Edge-Conditional Edge 边界 / Edge-Scheduler 关系）
- [x] PR #33 复审通过并 squash merge 到 main（commit 6f7c33f，CI build/test 双绿，2026-08-05）→ Chapter 11 最终完成
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #33 创建。
- 2026-08-05：**PR #33 Architecture Review 六项修正**（commit：docs: refine edge routing and error ownership boundaries）全部应用并推送更新 PR #33：
  1. **Routing error 归属修正**：route_by_next_action 非法 next_action 抛 application-defined routing error——应用 callable 产生、Graph Runtime 调用与传播、应用级 invoke 兜底构造 FAILED State；不是 LangGraph 自动业务错误转换、不称 Graph Runtime 内部错误（11.7 / Q7 / 11.9 / 验收标准）
  2. **Conditional Edge 两层定义**：概念层（routing callable → Graph Runtime 可解释的路径结果）+ 当前 Demo（符号化 route key + path map）；path map 不是必经结构（11.3 / 11.4 Mermaid / Q3 / Q4 / 总结 / 验收标准）
  3. **next_action 作用域收窄**：写入 State 是当前 Demo 的显式契约设计非框架强制（四项收益；"为 Trace/审计提供可记录依据"非"已实现审计"）；Command 留 ch13；误区 #6 重写（11.5 / Q6 / 误区 #6）
  4. **Route Decision 纯函数三层**：定义 = State + runtime facts → 路径结果；工程推荐 = 确定性/无副作用/可测/依赖显式化；Demo 事实 = 实现并测试为纯函数；"纯函数化"不是定义组成部分（11.4 表格 / Q4 / 验收标准）
  5. **Edge / Conditional Edge 边界**：普通静态 Edge 不读 State 不判断；读取 State 的是 routing callable；declaration 与 callable 都不执行 Node（11.2 / 11.3 / 误区 #1）
  6. **Edge / Scheduler 关系**：三层（declaration / routing callable / Graph Runtime-Scheduling Execution）；"Edge 是 Runtime 控制流的声明载体，不是 Scheduler 本身"（11.1 / Q1 / Q4 / 总结）
- 2026-08-05：PR #33 经 Architecture Review 复审通过，squash merge 到 main（commit 6f7c33f，CI build/test 双绿）→ **TASK-0018 标记 completed；Chapter 11 最终完成**；本 Memory PR（docs/post-pr33-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
