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
- [ ] LangGraph 等价 Demo
- [ ] 官方参考索引

## v0.3.0：Agent 与 Runtime 基础

- [x] Agent Runtime Design Principles（docs/99-design-principles/，待架构审查）
- [ ] LLM 与 Agent
- [ ] Agent Loop
- [ ] Runtime
- [ ] State
- [ ] Tool Registry
- [ ] Prompt Builder
- [ ] Memory 与 Context
- [ ] 手写 Runtime

## v0.4.0：LangGraph Core

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
