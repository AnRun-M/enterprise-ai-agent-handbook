# TASK-0013：Chapter 07《Memory、Context 与 Context Management》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 2-6 章、.ai/principles/architecture-map.md（第三/四/五层） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph（State/History 正例、Memory 反例） |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph（不验证 Memory/Context Management——如实标注） |

## 目标

编写 Part 02 最后一个规划章节 `docs/02-agent-runtime/ch07-memory-context-management.md`：讲清 Memory / State / Model Context / Checkpoint 边界与 Context Management 基础 Runtime 语义。Part 02 收官前置。

## 需要新增

- `docs/02-agent-runtime/ch07-memory-context-management.md`（7.1-7.11，回答 Q1-Q10，6 张 Mermaid 图）
- `.ai/tasks/TASK-0013-chapter-07-memory-context-management.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Runtime 导航加入第 7 章）
- `docs/02-agent-runtime/index.md`（主题表 + 章节列表）
- `ROADMAP.md`（v0.3.0 Chapter 07 draft 勾选）
- `docs/00-introduction/content-map.md`（第 7 章行状态）
- `.ai/context/current.md`

## 约束

- 不讲向量数据库 / Embedding / RAG 算法 / BM25 / Knowledge Graph / MCP / LangGraph Memory-Checkpointer API / 数据库实现 / 长期记忆产品
- Demo 无 Memory / Context Manager 必须如实标注（正例 / 反例 / 未来输入来源）
- 不修改 architecture-map / principles / ADR / 已完成章节 / examples / tests / 依赖
- 不把 Part 02 标为最终完成（收官检查在 Merge 后的 Memory PR 中执行）

## 验收标准

- [x] 章节结构 7.1-7.11 完成，Q1-Q10 全部回答
- [x] 6 张 Mermaid 图（四概念关系 / 跨轮 vs 跨执行判定 / Pipeline / Builder-Manager 边界 / Memory 写入生命周期 / Injection 来源）
- [x] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过
- [ ] PR 创建并等待架构审查（不 Merge）
- [ ] Architecture Review 通过
- [ ] PR Merge 到 main
- 合并后方可标记 completed
