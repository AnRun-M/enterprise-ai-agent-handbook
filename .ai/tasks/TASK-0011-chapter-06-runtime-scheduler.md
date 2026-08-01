# TASK-0011：Chapter 06《Runtime Scheduler & Runtime Orchestration》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 1-5 章、.ai/principles/runtime-design.md、architecture-map.md（第六层） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

编写 Part 02 收官章节 `docs/02-agent-runtime/ch06-runtime-scheduler.md`：回答"Runtime 如何调度整个 Agent 的执行过程"。主线：Loop 负责继续、Scheduler 负责下一步；调度对象是 State Transition。建立完整 Runtime Control Plane 架构（Loop → State → Context → Builder → Registry → Scheduler），作为 Part 03 的自然桥梁。

## 需要新增

- `docs/02-agent-runtime/ch06-runtime-scheduler.md`（6.1-6.10，回答 Q1-Q10，4 张 Mermaid 图）
- `.ai/tasks/TASK-0011-chapter-06-runtime-scheduler.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Runtime 导航加入第 6 章）
- `docs/02-agent-runtime/index.md`（章节列表）
- `ROADMAP.md`（v0.3.0 Chapter 06 draft 勾选）
- `docs/00-introduction/content-map.md`（第 6 章行）
- `.ai/context/current.md`

## 约束

- 不提前讲 LangGraph API / Node / Edge / Checkpoint / Interrupt / Reducer / Send / Command
- 不把 Scheduler 写成 Workflow Engine；Loop 与 Scheduler 必须彻底区分
- 不新增 Python / Demo；引用前五章与 principles，不复制定义
- Demo 无独立 Scheduler 必须如实标注（隐式雏形）

## 验收标准

- [x] 章节结构 6.1-6.10 完成，Q1-Q10 全部回答（Q10 由本章补定义为收官问题：Part 02 Runtime 全景统一）
- [x] 4 张 Mermaid 图（Control Plane 总图 / 调度循环 / 组件编排 / 职责边界）
- [x] `mkdocs build --strict`、`pytest`、`ruff check .` 通过
- [x] PR #20 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（八项修正：Loop/Scheduler/Lifecycle 关系 / 调度对象=可执行步骤 / Workflow 非对立 / Routing Decision vs Scheduling Execution / 替换结论收窄 / 总图重画 / Part 02 定位修正 / PR 描述同步）
- [x] PR #20 squash merge 到 main（commit c50247a），远程 feature/chapter-06-runtime-scheduler 已删除
- 合并后方可标记 completed（本次已合并）
