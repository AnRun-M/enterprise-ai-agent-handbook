# TASK-0023：Chapter 16《Stream——流式输出》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-06 |
| Updated | 2026-08-06 |
| Related ADR | ADR-0001 / ADR-0003 |
| Related Chapter | 第 2 章（history）、第 8 章（集成点）、第 11 章（路由）、第 12 章（Reducer / history）、第 14 章（Checkpoint）、第 15 章（Interrupt，正交）；TASK-0014（Part 03 规划，ch16 定位） |
| Related Example | examples/basic_langgraph（agent.py：仅同步 invoke） |
| Related Test | 无（Demo 未使用，如实标注；证据为同步 invoke 代码事实 / 官方核验记录） |

## 目标

编写 Part 03 第八个原语章 `docs/03-langgraph-core/ch16-stream.md`：回答「调用方如何在图仍在执行时持续接收运行进展与增量输出？」。**核心主线固定（用户 2026-08-06 指定，写作不得偏离）**：Stream 让调用方在图仍在执行时持续接收运行进展与增量输出；它是观察和交付协议，不决定路由、不修改业务状态，也不等于日志系统。Graph Runtime 产生流事件，应用选择消费模式、展示方式与背压策略；Stream 与 Interrupt 正交，一个解决"边跑边看"，一个解决"暂停后再继续"。

## 需要新增

- `docs/03-langgraph-core/ch16-stream.md`（16.1-16.9 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0023-chapter-16-stream.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 16 章）
- `docs/03-langgraph-core/index.md`（第 16 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 16 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 16 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 / Part 03 已建立语义（ch02 history / ch11 路由 / ch12 Reducer / ch15 Interrupt），再讲 Stream 承载；禁止从 API 出发解释概念
- **三条硬边界**：不决定路由（观察协议，路由属 ch11）；不修改业务状态（只读观察 + 交付，State 更新仍走 Node Update + Graph Runtime 合并）；不等于日志系统（交付协议 vs 排障 / 审计记录，architecture-map Observability）
- **最终 State 仍是权威结果**：流事件是过程视图；history 在 State 内（行为判断与测试）vs 流事件（交付过程视图）
- **消费决策在应用**：Graph Runtime 产生流事件；消费模式 / 展示方式 / 背压策略由应用选择（传输语义属 Part 05）
- **与 Interrupt 正交**：边跑边看（不暂停、不改变执行）vs 暂停后再继续；可共存、互不依赖
- **不提前展开**：astream / astream_events API 写法（框架 API 教程）、生产流式交付（SSE / WebSocket / 部分输出策略 / 前端呈现——Part 05）、流式下 HITL 交互（Part 05）、token 级流（LLM 内部，不属于图执行层）、Subgraph 嵌套流（ch17，仅引用）
- **当前 Demo 未使用**：如实标注（agent.py 仅同步 invoke / references 核验记录 / architecture-map 概念坐标）
- **证据诚实**：仓库无 Stream 实现证据——基于同步 invoke 代码事实与官方核验记录；未验证清单 6 项如实标注；不推断实现行为
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-15、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 16.1-16.9 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持
- [ ] 5 张 Mermaid 图（同步 invoke vs 流式 / 流事件类型与最终 State / Stream 三条硬边界 / 消费模式与背压（应用契约）/ Stream 与 Interrupt 正交）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0023 Status = in_progress；ROADMAP Chapter 16 = draft / 待架构审查；content-map 第 16 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-16-stream，commit `docs: draft chapter 16 stream`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-06：任务创建，正文初稿完成（待补）
