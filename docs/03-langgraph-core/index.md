# Part 3：LangGraph Core

> Part 03 不是介绍 LangGraph，而是回答：**Runtime 在 LangGraph 中的承载方式**。所有 Runtime 概念已在 Part 02 定义（State / Context / Memory / Scheduler / Tool Registry），本 Part 只引用，不重新定义。

## 章节

- [第 8 章：为什么是图——为什么 Runtime 可以用 Graph 表达](ch08-why-graph.md)（定位章：执行控制结构可图化；Graph Representation vs LangGraph Runtime）
- 第 9 章：Graph State（状态 schema 定义图）
- 第 10 章：Execution Nodes（Node 执行模型）
- 第 11 章：Edge & Conditional Edge（静态边与条件路由）
- 第 12 章：Reducer（状态合并语义）
- 第 13 章：Command & Send（动态控制流）
- 第 14 章：Checkpoint（持久化与恢复）
- 第 15 章：Interrupt（暂停与人工介入）
- 第 16 章：Stream（流式输出）
- 第 17 章：Subgraph（图组合与复用）

## 全局参考

- [手写 Runtime vs LangGraph：一一对照](manual-vs-langgraph.md)（对照速览，v0.4.0 里程碑前的先行文档）
- Runtime → LangGraph 全映射（Part 03 全局参考，落成中）
