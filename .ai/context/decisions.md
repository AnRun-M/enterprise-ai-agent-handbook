# Long-term Decisions

## ADR-001：Architecture First

原因：AI Coding 降低了 API 记忆价值，但架构判断、边界识别、状态设计和代码审查仍然是核心能力。

## ADR-002：Text-to-SQL 是唯一贯穿主案例

原因：减少认知切换，让每个抽象都能回到真实业务。

## ADR-003：LangGraph 是核心实践框架，但不是唯一主题

原因：项目目标是理解 Agent Runtime，而不是绑定某个框架。

## ADR-004：确定性约束优先由代码保证

包括：

- SQL 安全
- 权限校验
- 输出格式
- 超时
- 行数限制
- 引擎路由
- 重试策略

## ADR-005：Prompt 不承担全部业务规则

规则应拆分为：

- 常驻系统约束
- 动态检索规则
- 结构化语义层
- 程序化校验
- 用户会话上下文

## ADR-006：AI 协作依赖仓库记忆，不依赖聊天记忆

所有 AI 必须读取 `.ai/context/` 和 `AGENTS.md`。
