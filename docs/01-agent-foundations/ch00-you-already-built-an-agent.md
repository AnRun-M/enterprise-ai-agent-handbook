# 第 0 章：你已经写了一个 Agent，只是你不知道

> 状态：待正式编写

## 本章目标

回答：

> 通过 HTTP 调用 LLM、注入 Prompt、注册 Tool、循环执行 Tool Call 的 Text-to-SQL 系统，究竟算不算 Agent？

初步结论：

- 它已经具备 Agent 的最小闭环
- 它的 Runtime 是手写的
- 框架不会消灭 Loop，只会把状态、控制流和恢复机制显式化
- 是否需要 LangGraph，取决于复杂度、恢复、可观测和多人协作需求
