# TASK-0015：Chapter 08《为什么是图：为什么 Runtime 可以用 Graph 表达》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-03 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 1 章（Loop）、第 2 章（Execution State）、第 6 章（Scheduler & Orchestration）、第 7 章；TASK-0014（Part 03 规划） |
| Related Example | examples/basic_langgraph（README 第 16/17/18 节）、examples/manual_agent_loop |
| Related Test | tests/basic_langgraph（`test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 定位章 `docs/03-langgraph-core/ch08-why-graph.md`：回答「**为什么 Runtime 可以用 Graph 表达**」这一前置问题，为后续原语章（ch09-ch17）提供统一的思考框架。**不承担索引职责**（Runtime → LangGraph 映射表是 Part 03 全局参考，不属于本章正文）。

## 需要新增

- `docs/03-langgraph-core/ch08-why-graph.md`（8.1-8.9 结构，回答 Q1-Q10，4 张 Mermaid 图）
- `.ai/tasks/TASK-0015-chapter-08-why-graph.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 8 章）
- `docs/03-langgraph-core/index.md`（章节列表 + 第 8 章条目）
- `docs/00-introduction/content-map.md`（新增第 8 章行，状态「进行中/正文初稿」）
- `ROADMAP.md`（v0.4.0 标注 Chapter 08 draft）
- `.ai/context/current.md`

## 约束

- **只回答「LangGraph 如何承载 Runtime」**：Runtime 第一视角、Framework 第二视角；先解释 Runtime 语义，再解释 LangGraph 如何实现；禁止从 API 出发解释概念
- **禁止重新定义** State / Context / Memory / Scheduler / Tool Registry——只能引用 Part 02 章节（ch01/ch02/ch06/ch07 与 architecture-map）
- 不复制 Runtime → LangGraph 映射表（全局参考）；不介绍任何单个 LangGraph API 的写法（ch09-ch17 职责）
- 不提前讲 Part 05 生产语义（Checkpoint/Interrupt/Stream 只作为挂载点提及）、不涉及 MCP/A2A
- Demo 如实标注：Checkpoint / Interrupt / Stream / Send / Command / Subgraph 在 basic_langgraph 均未使用
- 遵守 ADR-0001（先动机后 API）、ADR-0003（LangGraph 是核心框架但不是唯一主题）、architecture-map（Part 01-03 归属）、runtime-design（三层职责）、state-design（State 边界）
- 术语与 `TERMINOLOGY.md` 一致（首次出现「中文（English）」）；流程引用 canonical-pipeline / manual-vs-langgraph

## 验收标准

- [x] 章节结构 8.1-8.9 完成，Q1-Q10 全部回答
- [x] 主线明确：执行控制结构可图化（循环显式 / 连接可声明 / 执行结构可审查）；LangGraph Runtime 提供 Checkpoint / Interrupt / Streaming 集成机制
- [x] 每节先 Runtime 语义后 LangGraph 承载，无 API 先行的解释
- [x] 4 张 Mermaid 图（while vs 图回路 / LangGraph Runtime 集成点 / 图带来与没带来 / 执行控制关切→图原语概念映射）
- [x] `mkdocs build --strict`、`git diff --check` 通过；全量测试在 CI 中通过（具体数量以最新 CI 为准）；`ruff check .` 通过
- [x] content-map / ROADMAP / index / mkdocs 四源更新
- [x] PR #27 创建
- [x] Architecture Review 通过（八项修正全部应用）
- [x] CI 双绿（build / test）
- [x] PR #27 squash merge 到 main（commit 2a19809，2026-08-05）
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-03：任务创建，开始正文初稿。
- 2026-08-03：正文初稿完成 `docs/03-langgraph-core/ch08-why-graph.md`（8.1-8.9，Q1-Q10，4 张 Mermaid 图）；四源更新完成；mkdocs build --strict / git diff --check / pytest / ruff 全过。PR #27 创建，待 Architecture Review。
- 2026-08-05：**PR #27 Architecture Review 修正**（commit：docs: refine graph runtime boundaries and note langchain scope），八项全部应用：
  1. **8.6 执行控制关切范围**：改为「为什么 Runtime 的核心执行控制关切能够用图表达」——区分两类关切（可直接映射图原语的执行控制结构 vs 作为节点依赖 / 输入来源 / 外围能力参与的 Context / Registry / Memory / Policy / 外部事实源）；删除「每个 Runtime 概念都能入图」绝对化表述
  2. **Graph Representation vs LangGraph Runtime**：整章主线调整；循环可显式 / 连接可声明 / 执行结构可审查属 Graph Representation，Checkpoint / Interrupt / Streaming 是 LangGraph Runtime 提供的能力；普通图 / DAG / 状态机不天然具备 durable execution；集成点 ≠ 能力自动生效；8.4 改题为「LangGraph Runtime：运行时能力有明确集成点」
  3. **Routing 纯函数表述收窄**：改为「当前 Demo 将路由决策函数设计为纯函数，是可测试与可重放的工程选择，不是 LangGraph 强制约束」；依赖（request-scoped config / feature flags / quota / policy result / runtime facts）应显式化
  4. **TASK-0003 验证结论收窄**：改为「最终 State 关键字段、终止行为和 history 动作序列上保持观察等价」；明确未验证 concurrency / side-effect ordering / retry / checkpoint-recovery / delivery / 一般性 Runtime 可替换
  5. **Agent Loop 映射修正**：改为「编译后图的执行过程 + 条件边回路 + Lifecycle / Termination Guard」；StateGraph 构建器 ≠ Agent Loop
  6. **「固定边界」表述收窄**：改为「LangGraph 提供明确集成机制与执行协议，应用不必从零设计基础接入方式」；框架不自动提供业务恢复策略 / 审批权限 / 幂等补偿审计（属 Part 05）
  7. **LangChain 边界提示**：本章边界新增技术栈边界（LangGraph 可独立使用；LangChain 为更高层抽象；create_agent 使用 LangGraph 作为图式 Agent Runtime；后续独立 Scope Planning），不展开实现
  8. **Future LangChain Scope Planning 记录**：`.ai/context/current.md` 新增 future task（不立即执行，不改 ROADMAP / content-map / mkdocs，Part 03 完成后单独创建 Scope Alignment 任务）
- 2026-08-05：PR #27 经 Architecture Review 复审通过，squash merge 到 main（commit 2a19809，CI build/test 双绿）→ **TASK-0015 标记 completed；Chapter 08 最终完成**；本 Memory PR（docs/post-pr27-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
