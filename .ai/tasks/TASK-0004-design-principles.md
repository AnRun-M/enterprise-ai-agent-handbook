# TASK-0004：建立《Agent Runtime Design Principles》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 0 章、docs/03-langgraph-core/manual-vs-langgraph.md |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

在 manual_agent_loop 与 basic_langgraph 完成后，总结本项目**已经验证过**的设计原则，形成整个仓库未来所有代码、章节、Demo 的统一设计规范（项目宪法）。所有原则必须能引用已有代码 / PR / Review / ADR，不新增任何新理论。

## 需要新增

- `.ai/principles/`：index / runtime-design / state-design / llm-vs-runtime / testing-agent / review-checklist（PR #5 Review 后由 docs/99-design-principles/ 迁入：内部规范，不属于出版内容，不进 MkDocs）
- `.ai/tasks/TASK-0004-design-principles.md`（本文件）

## 需要修改

- `AGENTS.md`（强制读取顺序加入 `.ai/principles/index.md`）
- `ARCHITECTURE.md`（内容边界：`.ai/principles/` 为内部设计规范）
- `ROADMAP.md`（v0.3.0 新增 Design Principles 里程碑项，描述为内部规范）
- `.ai/context/current.md`

## 约束

- 每条原则必须来自：第 0 章 / Manual Runtime / LangGraph Runtime / PR Review / Architecture Review / ADR
- 禁止："我认为 / 最佳实践 / 推荐"式表述；必须回答为什么，不是怎么做
- 不新增任何新的架构思想，不发明新理论

## 验收标准

- [x] 六份文档完成，全部原则可溯源到已有产物
- [x] `mkdocs build --strict` 通过
- [x] `ruff check .`、`pytest` 通过
- [ ] PR 创建并等待架构审查（不 Merge）
- [ ] Architecture Review 通过
- [ ] PR Merge 到 main
- 合并后方可标记 completed
