# ADR-0002：Text-to-SQL 作为唯一贯穿主案例

## 状态

Accepted

## 背景

大量教程使用天气、笑话等 Demo，无法覆盖权限、安全、执行成本、恢复和业务口径问题。

## 决策

使用 Text-to-SQL 作为全书唯一贯穿主案例。

## 影响

所有 Agent Runtime、LangGraph、MCP、A2A 示例优先映射到 Text-to-SQL。
