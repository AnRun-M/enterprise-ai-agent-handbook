# TASK-0016：Chapter 09《Graph State——状态如何进入图》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
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
- **完整 Initial State 是本 Demo 的设计选择与测试契约，不是 LangGraph 普遍强制要求**（LangGraph 支持独立 input/output schema 与 internal / private state）；禁止写"框架要求初始输入包含所有 State 字段"
- **StateProxy 是属性访问适配器**：按只读约定使用，但不提供强制不可变保证、不是权限/安全边界、不等于 Model Context（当前 Demo 无独立 Context Builder）
- **Graph State 可见范围两层**：当前 Demo 所有节点同一输入 schema；LangGraph 通用能力支持 input/output schema 划分与 internal/private state——不是所有节点天然看见所有内部字段
- **Checkpoint 定义**：图执行时刻持久化的状态与执行上下文快照（Graph State 字段值是其核心组成部分，但不等于简单字典副本）；结构机制留第 14 章
- **字段生命周期归属三层**：应用设计定契约 / Node-Edge-Lifecycle Guard-Graph Runtime 在执行中实现演化 / schema 只声明形态与 reducer 挂载点
- **测试证据归属**：`test_router_*_is_pure` 只覆盖两个路由 callable 不修改输入；Node 输入不可变性无统一测试，不得用路由测试证明
- **TypedDict 静态检查为"提供条件"非"实际门禁"**：当前 CI 未启用 mypy --strict，不宣称所有错误提交前必被发现
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
- [x] PR #29 Architecture Review 七项修正全部应用（Initial State 框架误述 / StateProxy 只读收窄 / Graph State 可见范围 / Checkpoint 定义 / 生命周期归属 / 测试证据归属 / TypedDict 静态检查表述）
- [x] PR #29 复审通过并 squash merge 到 main（commit 06ea299，CI build/test 双绿，2026-08-05）→ Chapter 09 最终完成
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #29 创建。
- 2026-08-05：**PR #29 Architecture Review 七项修正**（commit：docs: refine graph state schema and visibility boundaries）全部应用并推送更新 PR #29：
  1. **Initial State 框架误述修正**：完整 Initial State 是本 Demo 的设计选择与测试契约，不是 LangGraph 普遍强制要求（LangGraph 支持独立 input/output schema、internal/private state）；新增常见误区 #11
  2. **StateProxy 只读表述收窄**：属性访问适配器（持有底层引用、无 setter），教学语义按逻辑只读；不提供强制不可变保证、不是权限/安全边界、不等于 Model Context；"模型只能读不能写"改为"模型适配路径按只读约定使用"；新增常见误区 #12
  3. **Graph State 可见范围收窄**：两层表述——当前 Demo 所有节点同一输入 schema；LangGraph 通用能力支持 input/output schema 与 internal/private state；主线与 9.4 增加推荐表述"具体节点可读取哪些字段取决于 schema 划分和节点输入契约"
  4. **Checkpoint 定义修正**：图执行时刻持久化的状态与执行上下文快照（Graph State 字段值是其核心组成部分，但不等于简单字典副本）；不展开 metadata / storage / thread / replay
  5. **生命周期归属修正**：应用设计定契约（语义/类型/合法状态/生命周期契约）、Node/Edge/Lifecycle Guard/Graph Runtime 执行中实现演化、schema 只声明形态不执行规则
  6. **测试证据归属修正**：路由纯函数测试只覆盖两个路由 callable；Node 输入不可变性无统一测试，如实标注（9.7 误解、9.9 证据表与未验证清单、Q8/Q10）
  7. **TypedDict 静态检查表述收窄**："为静态检查提供条件，是否成门禁取决于配置"；CI 未启用 mypy --strict；不宣称提交前必发现
- 2026-08-05：PR #29 经 Architecture Review 复审通过，squash merge 到 main（commit 06ea299，CI build/test 双绿）→ **TASK-0016 标记 completed；Chapter 09 最终完成**；本 Memory PR（docs/post-pr29-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
- 2026-08-05：记录 future maintenance（不立即执行）：修正 `examples/basic_langgraph/state.py` 中 `build_initial_state` docstring「LangGraph 要求初始 invoke 提供全部字段」→「构造本 Demo 约定的完整初始状态」（属于 examples 文档修正，不属于 Chapter 09，随 examples 维护任务处理）。
