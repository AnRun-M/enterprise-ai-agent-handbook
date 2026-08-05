# ROADMAP

## 版本规则

- ROADMAP 中的版本表示目标里程碑（进行中）；CHANGELOG 中的版本表示已经正式完成的版本。
- 未完成版本只能放在 CHANGELOG 的 `Unreleased` 中。
- 发布条件：
  - 对应里程碑全部完成
  - 文档构建通过（`mkdocs build --strict`）
  - 已有代码测试通过（`pytest`）
  - `.ai/context/current.md` 已更新
  - `CHANGELOG.md` 已更新

## v0.2.0：AI-Native 骨架

- [x] `.ai/` 上下文与任务目录
- [x] ADR 目录
- [x] MkDocs 配置
- [x] 文档、示例、测试骨架
- [x] 骨架收敛重构（ADR 单一事实源、canonical 流程、协作规范、命名与目录收敛）
- [x] 第 0 章
- [x] 手写 Agent Loop Demo
- [x] LangGraph 等价 Demo
- [ ] 官方参考索引

## v0.3.0：Agent 与 Runtime 基础

- [x] Agent Runtime Design Principles（.ai/principles/ 内部规范）
- [x] Runtime Architecture Map（.ai/principles/ 内部规范）
- [x] Chapter 01：Agent Loop
- [x] Chapter 02：Execution State
- [x] Chapter 03：Model Context
- [x] Chapter 04：Prompt Builder
- [x] Chapter 05：Tool Registry
- [x] Chapter 06：Runtime Scheduler & Orchestration
- [x] LLM 与 Agent（由 Chapter 00 / 03 覆盖）
- [x] Agent Loop（Chapter 01）
- [x] Runtime（Chapter 02-06 体系 + Chapter 06 编排总览）
- [x] State（Chapter 02）
- [x] Tool Registry（Chapter 05）
- [x] Prompt Builder（Chapter 04）
- [x] 手写 Runtime（已满足：manual_agent_loop Demo + Chapter 01-06 + Runtime Architecture Map）
- [x] Chapter 07：Memory、Context 与 Context Management（最终完成；Part 02 收官）

> v0.3.0 全部完成（2026-08-01）：Agent 与 Runtime 基础里程碑——Chapter 01-07 最终完成，Part 02 最终完成。

## v0.4.0：LangGraph Core

- [x] Chapter 08：为什么是图——为什么 Runtime 可以用 Graph 表达（最终完成，2026-08-05，PR #27）
- [x] Chapter 09：Graph State——状态如何进入图（最终完成，2026-08-05，PR #29）
- [x] Chapter 10：Execution Nodes——Node 执行模型（最终完成，2026-08-05，PR #31）
- [x] Chapter 11：Edge 与 Conditional Edge——静态边与条件路由（最终完成，2026-08-05，PR #33）
- [ ] Chapter 12：Reducer——状态合并语义（draft / 待架构审查，2026-08-05）
- [ ] StateGraph
- [ ] Node
- [ ] Edge
- [ ] Conditional Edge
- [ ] Reducer
- [ ] Command
- [ ] Send
- [ ] Checkpoint
- [ ] Interrupt
- [ ] Stream
- [ ] Subgraph

## v0.5.0：Text-to-SQL 重构

- [ ] Text2SQLState
- [ ] 意图识别
- [ ] 元数据检索
- [ ] 业务规则检索
- [ ] SQL 生成
- [ ] SQL 校验
- [ ] 权限检查
- [ ] 引擎路由
- [ ] SQL 修复循环
- [ ] Python 分析
- [ ] 结构化输出

## v0.6.0：生产级能力

- [ ] Checkpoint
- [ ] Human-in-the-loop
- [ ] 幂等
- [ ] Retry
- [ ] Timeout
- [ ] Compensation
- [ ] Observability
- [ ] Cost Control
- [ ] Evaluation
- [ ] Regression Test

## v0.7.0：MCP 与 A2A

- [ ] MCP 边界
- [ ] MCP Tool 接入
- [ ] A2A 边界
- [ ] Agent Card
- [ ] Task / Artifact
- [ ] Text-to-SQL Agent 服务化

## v1.0.0

- 12 至 16 个核心章节
- 5 至 8 个递进式 Demo
- 完整 Text-to-SQL 参考实现
- 测试与文档站
- 官方资料核验
