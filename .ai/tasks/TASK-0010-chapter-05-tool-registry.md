# TASK-0010：Chapter 05《Tool Registry》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | 第 1-4 章、.ai/principles/architecture-map.md（第七层） |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 目标

编写 Part 02 第四章 `docs/02-agent-runtime/ch05-tool-registry.md`：回答"Runtime 如何管理 Agent 可调用的能力"。主线：Tool Registry 是管理"能力描述"与"执行映射"的注册表——不是工具集合本身，也不是模型决策器。

## 需要新增

- `docs/02-agent-runtime/ch05-tool-registry.md`（5.1-5.10，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0010-chapter-05-tool-registry.md`（本文件）

## 需要修改

- `mkdocs.yml`（Agent Runtime 导航加入第 5 章）
- `docs/02-agent-runtime/index.md`（章节列表）
- `ROADMAP.md`（v0.3.0 Chapter 05 draft 勾选）
- `docs/00-introduction/content-map.md`（第 5 章行）
- `.ai/context/current.md`

## 约束

- 不新增 Python / Demo / 修改现有示例 / ADR / principles
- 不引入 MCP SDK / LangGraph ToolNode；不写生产级权限、Retry、Timeout、Sandbox 实现
- 不把 Registry 写成模型决策器 / Tool Executor；不把 MCP 等同 Registry
- Demo 未实现 Registry 必须如实标注（架构抽象）

## 验收标准

- [x] 章节结构 5.1-5.10 完成，Q1-Q10 全部回答
- [x] 5 张 Mermaid 图（位置 / 双视图 / Tool Call 路径 / 权限纵深防御 / schema 版本影响）
- [x] `mkdocs build --strict`、`pytest`、`ruff check .` 通过
- [x] PR #18 创建并等待架构审查（不 Merge）
- [x] Architecture Review 通过（六项修正：Registry 与 Tool View 分离 / Dispatcher 完整路径 / 术语固定 / canonical definition + Provider Adapter / 判别式 Result Contract / 纵深防御最终边界）
- [x] PR #18 squash merge 到 main（commit 483b636），远程 feature/chapter-05-tool-registry 已删除
- 合并后方可标记 completed（本次已合并）
