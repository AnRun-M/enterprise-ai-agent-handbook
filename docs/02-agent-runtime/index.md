# Part 2：Agent Runtime

## 主题覆盖与归属（TASK-0012 范围对齐）

| 主题 | 归属 | 状态 |
|---|---|---|
| Execution State | Part 02 | Chapter 02 ✅ |
| Model Context | Part 02 | Chapter 03 ✅ |
| Prompt Builder | Part 02 | Chapter 04 ✅ |
| Tool Registry | Part 02 | Chapter 05 ✅ |
| Scheduler / Orchestration | Part 02 | Chapter 06 ✅ |
| Memory 与 Context / Context Management | Part 02 | Chapter 07 ✅（draft，待架构审查） |
| Agent Loop | Part 01 | Chapter 01 ✅（本 Part 引用） |
| Retry | Part 05（生产级） | 概念边界见 Chapter 01（Retry ≠ Loop） |
| Checkpoint | Part 03（Checkpointer 机制）+ Part 05（生产恢复语义） | 边界见 architecture-map |
| Interrupt | Part 03（原语）+ Part 05（HITL 语义） | 边界见 Chapter 01（Human Stop 暂停态） |
| Streaming | Part 03（Stream API / 框架机制）+ Part 05（生产流式交付与运行语义） | — |
| Trace | Part 05（Observability） | — |

## 章节

- [第 2 章：Execution State](ch02-execution-state.md)
- [第 3 章：Model Context](ch03-model-context.md)
- [第 4 章：Prompt Builder](ch04-prompt-builder.md)
- [第 5 章：Tool Registry](ch05-tool-registry.md)
- [第 6 章：Runtime Scheduler & Runtime Orchestration](ch06-runtime-scheduler.md)
- [第 7 章：Memory、Context 与 Context Management](ch07-memory-context-management.md)

后续章节待规划，见 [章节—示例—测试映射](../00-introduction/content-map.md)。
