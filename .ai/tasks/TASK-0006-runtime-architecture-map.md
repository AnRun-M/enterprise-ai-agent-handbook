# TASK-0006：建立《Runtime Architecture Map》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0001 ~ ADR-0006 |
| Related Chapter | Part 01-03（全局坐标系，非读者章节） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

新增内部设计规范 `.ai/principles/architecture-map.md`：为 Part 01 ~ Part 03 固定统一坐标系，避免 State / Context / Memory / Checkpoint / Interrupt / Streaming 等章节发生概念边界漂移。非出版内容，不进 MkDocs，不写 Chapter 02 正文，不新增 Demo / Python / 未经验证理论。

## 需要新增

- `.ai/principles/architecture-map.md`（八层总览 + 总图 + 边界表 + 判定问题 + Part 01-03 归属 + T01-T12 映射 + 单一事实源规则）
- `.ai/tasks/TASK-0006-runtime-architecture-map.md`（本文件）

## 需要修改

- `.ai/principles/index.md`（新增 architecture-map 链接 + 阅读规则）
- `ARCHITECTURE.md`（一行：architecture-map 是内部概念坐标）
- `ROADMAP.md`（v0.3.0 内部前置项）
- `.ai/context/current.md`

## 约束

- 全部结论来自已有代码 / ADR / Principles / 第 0-1 章，或明确标记为待验证
- 不选型 Memory 数据库 / Checkpoint Store / Workflow Engine
- 不把 LangGraph 实现当作唯一架构；不合并 State/Context/Memory/Checkpoint
- 不复制大段 TERMINOLOGY / canonical pipeline 内容；不加入 MkDocs 导航；不修改 Demo / 依赖 / ADR

## 验收标准

- [x] Architecture Map 完成（分层 / 总图 / 边界表 / 判定问题 / 章节归属 / pipeline 映射 / 单一事实源规则）
- [x] principles index 更新（含阅读规则）
- [x] 概念边界检查完成（State/Context/Memory/Checkpoint 未合并、未多源）
- [x] `mkdocs build --strict`、`pytest`、`ruff check .` 通过
- [x] Architecture Review 通过（四个 Blocker 全部修复并复审通过：Memory 边界改为跨越单次执行边界 / 总图改为职责关系与条件分支 / Checkpoint-Audit 收窄 / State 引用策略）
- [x] PR #10 squash merge 到 main（commit 48bca0e），远程 feature/runtime-architecture-map 已删除
- 合并前保持 in_progress（本次已合并）
