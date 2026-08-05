# TASK-0021：Chapter 14《Checkpoint——持久化与恢复》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 |
| Related Chapter | 第 1 章（Human Stop 暂停态）、第 2 章（State 快照引用）、第 7 章（Memory）、第 9 章（Graph State）、第 12 章（Reducer）、第 13 章（动态 work item）；TASK-0014（Part 03 规划，ch14 定位） |
| Related Example | examples/basic_langgraph（agent.py / graph.py：未启用 Checkpointer）、examples/checkpoint_hitl（预留） |
| Related Test | 无（Demo 未启用，如实标注；证据为 docstring / 官方核验记录） |

## 目标

编写 Part 03 第六个原语章 `docs/03-langgraph-core/ch14-checkpoint.md`：回答「图执行如何从"内存易失"变成"可恢复"？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Graph State 是执行中的当前状态；Checkpoint 是图在某个执行时刻持久化的状态与执行上下文快照。Checkpointer 负责保存和读取这些快照，使 Runtime 能够恢复、重放或继续执行；Checkpoint 不是 Memory，也不等于一个简单的 State 字典副本。

**三条核心边界（必须守住）**：① Graph State = 当前执行状态；Checkpoint = 执行时刻快照；② Checkpointer 负责保存 / 读取，但恢复策略、重放语义、续跑规则由 Runtime 与应用契约共同决定；③ Checkpoint 不是 Memory、不等于简单 State 字典副本。

## 需要新增

- `docs/03-langgraph-core/ch14-checkpoint.md`（14.1-14.11 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0021-chapter-14-checkpoint.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 14 章）
- `docs/03-langgraph-core/index.md`（第 14 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 14 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 14 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线与三条边界固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch02 State 快照边界 / ch07 Memory / architecture-map 第五节），再讲 Checkpoint 承载；禁止从 API 出发解释概念
- **Checkpointer 职责边界**：保存 / 读取快照 = Checkpointer；恢复策略 / 重放语义 / 续跑规则 = Runtime 与应用契约共同决定（集成点 ≠ 能力自动生效，第 8 章 8.4）
- **持久化内容**：Graph State 字段值（核心组成部分）+ channel 状态（含 reducer 累积，第 12 章衔接）+ 执行上下文——**不等于简单 State 字典副本**（第 9 章 9.8 修正表述）
- **Checkpoint ≠ Memory**（第 7 章区分轴：快照时刻 vs 跨执行边界）
- **Checkpoint 与 Interrupt**：承载基础关系（第 15 章依赖），本章只立边界
- **当前 Demo 未启用**：如实标注教学边界（graph.py 无 checkpointer / agent.py docstring / examples/checkpoint_hitl 预留 / references 核验记录 / architecture-map 未决项）
- **不提前展开**：Checkpointer API 写法与存储后端（框架 API 教程 / 实现细节）、生产恢复语义（HITL / 幂等 / 补偿 / 审计——Part 05）、Interrupt API（ch15）、Stream（ch16）、Subgraph（ch17）
- **证据诚实**：仓库无 Checkpoint 实现证据——基于 docstring / graph.py / 预留目录 / 官方核验记录；未验证清单如实标注（保存读取行为 / 崩溃恢复确定性 / 重放语义 / 续跑规则 / reducer 累积序列化 / 并发组合 / 生产恢复策略）；不推断实现行为
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-13、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 14.1-14.11 完成，Q1-Q10 全部回答
- [ ] 固定主线与三条核心边界逐字保持
- [ ] 5 张 Mermaid 图（执行流 + 快照时刻 / Graph State vs Checkpoint vs Memory 边界 / Checkpointer 保存读取与 Runtime 契约 / 持久化内容 / 恢复-重放-续跑）——图不暗示 Checkpointer 决定恢复策略
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0021 Status = in_progress；ROADMAP Chapter 14 = draft / 待架构审查；content-map 第 14 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-14-checkpoint，commit `docs: draft chapter 14 checkpoint`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
