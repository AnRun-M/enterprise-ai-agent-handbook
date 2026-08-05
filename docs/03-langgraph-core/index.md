# Part 3：LangGraph Core

> Part 03 不是介绍 LangGraph，而是回答：**Runtime 在 LangGraph 中的承载方式**。所有 Runtime 概念已在 Part 02 定义（State / Context / Memory / Scheduler / Tool Registry），本 Part 只引用，不重新定义。

## 章节

- [第 8 章：为什么是图——为什么 Runtime 可以用 Graph 表达](ch08-why-graph.md)（定位章：执行控制结构可图化；Graph Representation vs LangGraph Runtime）
- [第 9 章：Graph State——状态如何进入图](ch09-graph-state.md)（Execution State 的 LangGraph 承载：schema / 字段契约 / Initial State / START 与 END / 节点部分更新）
- [第 10 章：Execution Nodes——Node 执行模型](ch10-execution-nodes.md)（Graph Runtime 管理的执行单元：读 State / 执行能力 / Partial Update / Failure Boundary / Node ≠ Tool）
- [第 11 章：Edge 与 Conditional Edge——静态边与条件路由](ch11-edge-conditional-edge.md)（Edge 确定性连接 / Conditional Edge 运行时选路 / Route Decision 与调度执行 / 模型决策与路由分发边界 / Lifecycle Guard）
- [第 12 章：Reducer——状态合并语义](ch12-reducer.md)（Current + Incoming → Next；默认覆盖 vs 追加语义；Reducer 绑定 channel 更新语义；Node / Reducer / Graph Runtime 三方职责）
- [第 13 章：Command 与 Send——动态控制流](ch13-command-send.md)（Command：更新与导航绑定；Send：按数据动态 fan-out；二者是不同原语；与 Scheduler 的对应；静态图足够时不需要动态原语）
- [第 14 章：Checkpoint——持久化与恢复](ch14-checkpoint.md)（执行时刻的状态与执行上下文快照；Checkpointer 保存 / 读取，恢复策略由 Runtime 与应用契约决定；恢复 / 重放 / 续跑；≠ Memory、≠ 简单字典副本）
- 第 15 章：Interrupt（暂停与人工介入）
- 第 16 章：Stream（流式输出）
- 第 17 章：Subgraph（图组合与复用）

## 全局参考

- [手写 Runtime vs LangGraph：一一对照](manual-vs-langgraph.md)（对照速览，v0.4.0 里程碑前的先行文档）
- Runtime → LangGraph 全映射（Part 03 全局参考，落成中）
