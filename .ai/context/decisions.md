# Long-term Decisions（索引）

ADR 唯一事实源：`docs/adr/`（编号四位，如 ADR-0001）。本文件只保留索引、摘要与链接，不存储完整正文。

| ID | 标题 | 摘要 | 文件 |
|---|---|---|---|
| ADR-0001 | Architecture First | 先讲设计动机和架构边界，再讲 API | [ADR-0001-architecture-first.md](../../docs/adr/ADR-0001-architecture-first.md) |
| ADR-0002 | Text-to-SQL 是唯一贯穿主案例 | 减少认知切换，让每个抽象回到真实业务 | [ADR-0002-text2sql-main-case.md](../../docs/adr/ADR-0002-text2sql-main-case.md) |
| ADR-0003 | LangGraph 是核心实践框架，但不是唯一主题 | 理解 Agent Runtime 而非绑定框架 | [ADR-0003-langgraph-core-framework.md](../../docs/adr/ADR-0003-langgraph-core-framework.md) |
| ADR-0004 | 确定性约束优先由代码保证 | SQL 安全、权限、格式、超时、行数、路由、重试由程序保证 | [ADR-0004-deterministic-constraints-in-code.md](../../docs/adr/ADR-0004-deterministic-constraints-in-code.md) |
| ADR-0005 | Prompt 不承担全部业务规则 | 规则分层：系统约束、检索规则、语义层、程序校验、会话上下文 | [ADR-0005-prompt-does-not-own-all-business-rules.md](../../docs/adr/ADR-0005-prompt-does-not-own-all-business-rules.md) |
| ADR-0006 | AI 协作依赖仓库记忆，不依赖聊天记忆 | 所有 AI 必须读取 `.ai/context/` 与 `AGENTS.md` | [ADR-0006-repository-memory-over-chat-memory.md](../../docs/adr/ADR-0006-repository-memory-over-chat-memory.md) |
