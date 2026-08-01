# TASK-0012：Part 02 Runtime Scope Alignment

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-01 |
| Updated | 2026-08-01 |
| Related ADR | ADR-0003 / ADR-0004 / ADR-0005 / ADR-0006 |
| Related Chapter | Chapter 01-06、.ai/principles/architecture-map.md |
| Related Example | examples/manual_agent_loop、examples/basic_langgraph |
| Related Test | tests/manual_agent_loop、tests/basic_langgraph |

## 1. 当前不一致清单（三个规划事实源）

1. **ROADMAP v0.3.0 冗余未勾选项**：`Agent Loop` / `State` / `Tool Registry` / `Prompt Builder` 与已完成的 Chapter 01 / 02 / 05 / 04 重复；`LLM 与 Agent` 与 Chapter 00 / 03 概念重复；`Runtime` 与 Chapter 02-06 体系重复——均未标注"由章节覆盖"。
2. **ROADMAP 残留过时标注**：`Agent Runtime Design Principles（.ai/principles/ 内部规范，待架构审查）`——PR #5 早已合并，标注过期。
3. **Part 02 index 主题列表含移出主题**：`Retry`（生产级，Part 05）、`Checkpoint` / `Interrupt`（Part 03 机制 + Part 05 语义）、`Streaming`（Part 03 API + Part 05 传输）、`Trace`（Part 05 Observability）——按架构边界不属于 Part 02 基础语义。
4. **Part 02 index 缺 Model Context / Memory**：`Model Context` 已有 Chapter 03 但不在主题列表；`Memory 与 Context` 无对应章节。
5. **content-map Part 2 行状态过时**："进行中（Execution State 已完成）"——Chapter 02-06 均已最终完成。
6. **Chapter 07 未规划**：ROADMAP `Memory 与 Context` 项无章节载体；content-map 无对应行。

## 2. 主题归属矩阵

| 主题 | 正文 | Demo/测试 | Part 02 基础语义 | 移 Part 03 | 移 Part 05 | 独立章节 | 结论 |
|---|---|---|---|---|---|---|---|
| LLM 与 Agent | ch00 / ch03 | ✅ | — | — | — | 已覆盖 | 已满足 |
| Agent Loop | ch01 ✅ | ✅ | 是 | — | — | 已覆盖 | 最终完成 |
| Runtime | ch02-06 体系 + ch06 总览 ✅ | ✅ | 是 | — | — | 已覆盖 | 已满足 |
| Execution State | ch02 ✅ | ✅ | 是 | — | — | 已覆盖 | 最终完成 |
| Model Context | ch03 ✅ | 隐式（StateProxy） | 是 | — | — | 已覆盖 | 最终完成 |
| Prompt Builder | ch04 ✅ | 架构抽象（已标注） | 是 | — | — | 已覆盖 | 最终完成 |
| Tool Registry | ch05 ✅ | 架构抽象（已标注） | 是 | — | — | 已覆盖 | 最终完成 |
| Scheduler / Orchestration | ch06 ✅ | 路由函数测试 | 是 | — | — | 已覆盖 | 最终完成 |
| Context Management | 无正文 | 无 | 是（基础语义） | — | — | **并入 ch07** | 规划 |
| Memory 与 Context | architecture-map 边界 ✅（无章节） | 无 | 是（概念边界） | — | — | **ch07** | 规划 |
| Retry | ch01 概念边界（Retry≠Loop）；ch05 提及 Infrastructure | 无 | 概念边界已覆盖 | — | 生产实现（Retry/Backoff/Idempotency） | Part 02 不独立成章 | 移 Part 05 |
| Timeout | ch05 提及 | 无 | — | — | Part 05 | Part 05 | 移 Part 05 |
| Checkpoint | architecture-map 边界（State 快照）；ch02 引用 | 未启用 Checkpointer | 边界已覆盖 | Checkpointer 机制 | 生产恢复 / 持久化语义 | 不独立成章（边界已定义） | 拆两处 |
| Interrupt | ch01 Human Stop 暂停态；map | 无 | 边界已覆盖 | Interrupt 原语 | HITL 生产语义 | 不独立成章 | 拆两处 |
| Streaming | 无正文 | 无 | 输出流语义（可选留 Part 02） | Stream API | 生产流式交付与运行语义 | 拆三处，不独立成章 | 拆三处 |
| Trace | 无正文 | 无 | — | — | Observability（Part 05） | Part 05 | 移 Part 05 |
| 手写 Runtime | ch01-06 + manual Demo + Map ✅ | ✅ | 是 | — | — | 已覆盖 | 已满足 |
| Tool Execution Infrastructure | ch05 术语定义 | 无 | — | — | retry/timeout/sandbox/metrics | Part 05 | 移 Part 05 |

## 3. 已完成章节映射

| 章节 | 覆盖主题 |
|---|---|
| Chapter 01（Part 01） | Agent Loop、Workflow vs Agentic、终止、Retry≠Loop 概念边界 |
| Chapter 02 | Execution State |
| Chapter 03 | Model Context |
| Chapter 04 | Prompt Builder |
| Chapter 05 | Tool Registry、Dispatcher、Result Contract |
| Chapter 06 | Scheduler / Runtime Orchestration（阶段性编排总览） |

## 4. 剩余章节建议

**Chapter 07：Memory、Context 与 Context Management**（Part 02 唯一剩余必需章节）：

- 只讲：Memory 与 State / Context / Checkpoint 边界、Context Window、History、Compression、Trimming、Summarization、Injection、生命周期与事实源
- 不讲：具体向量数据库、检索算法、RAG 实现（后续章节）
- 前置：Chapter 03（Model Context 定义）、architecture-map（Memory 边界：区分轴=是否跨越单次执行边界）

## 5. 移出 Part 02 的主题

- **Part 05（生产级）**：Retry / Timeout / Backoff / Idempotency / Compensation（ROADMAP v0.6.0 已有对应项）、Trace / Observability、Tool Execution Infrastructure 生产实现
- **Part 03（LangGraph 承载）**：Checkpointer 机制、Interrupt 原语、Stream API、Reducer / Node / Edge 等图机制
- **拆两处**：Checkpoint（Part 03 机制 + Part 05 生产恢复语义）、Interrupt（Part 03 原语 + Part 05 HITL）、Streaming（Runtime 输出流语义可选留 Part 02 / Stream API Part 03 / 生产流式交付与运行语义 Part 05——不缩窄成协议层）

## 6. Part 02 是否可收官的结论

**暂不收官**。Chapter 07（Memory、Context 与 Context Management）完成后：ROADMAP v0.3.0 全勾、Part 02 index 对齐、content-map Part 2 行更新——届时可正式收官。Chapter 06 的"阶段性编排总览"定位与此一致（不提前宣布收官）。

## 7. ROADMAP / index / content-map 修改方案

- **ROADMAP v0.3.0**：Design Principles 去掉过期标注；冗余项标注"由 Chapter XX 覆盖"并勾选；`Memory 与 Context` 改为 `Chapter 07` 条目；`手写 Runtime` 标注已满足并勾选
- **Part 02 index**：主题列表改为"主题覆盖与归属"表（已覆盖 / 规划 / 移出标注）
- **content-map**：Part 2 行状态更新为"进行中（Chapter 02-06 已完成，Chapter 07 规划中）"；新增 Chapter 07 行（规划，v0.3.0）
- **current.md**：记录本任务结论

## 8. 风险与待验证项

1. **Chapter 07 的范围克制**：只讲基础语义与边界，不滑入向量库 / 检索 / RAG（写作任务书必须约束）
2. **Checkpoint / Interrupt / Streaming 的拆分**：Part 03 与 Part 05 各写什么需在各自 Part 规划时确认，避免两章重复
3. **"手写 Runtime 已满足"的判断**：以 manual Demo + ch01-06 + Map 为准；若 Review 认为需独立"手写 Runtime 全实现"章节，可重新评估（当前不成立）
4. **Part 02 收官时机**：ch07 合并后需再次对齐三源并更新 content-map Part 2 行

## 9. 本轮 Review 修正记录（PR #22 Architecture Review，2026-08-01）

1. **Chapter 06 摘要漂移修复**：content-map 第 6 章核心概念改为最终章节语义（Loop / Routing / Lifecycle Guard 边界、可执行步骤 / work item 调度、Control Plane 编排、Scheduler / Policy / LLM 职责边界、Runtime 替换契约与教学 Demo 验证范围）——不再写"Loop vs Scheduler"旧表述、"Scheduler 调度 State Transition"、无条件"Runtime 可替换"
2. **Chapter 07 证据列去预设**：对应示例 / 对应测试改为"待规划"——现有 Demo 与测试未实现或验证 Memory / Context Manager / Compression / Trimming / Summarization / Injection，不得把未来证据写成已存在事实
3. **Part 02 汇总范围换成正式目录**：content-map Part 2 行范围改为 Execution State / Model Context / Prompt Builder / Tool Registry / Runtime Scheduler & Orchestration / Memory、Context 与 Context Management；核心概念 / 对应测试同步更新；说明 Agent Loop 属 Part 01、手写 Runtime 已满足非独立章节、LLM 与 Agent 由 Chapter 00 覆盖
4. **Streaming 生产归属措辞收窄**：Part 05 侧由"生产传输协议"改为"生产流式交付与运行语义"，避免缩窄成协议层；Part 03 保留 Stream API / 框架机制
5. **三源一致性检查**：ROADMAP / Part 02 index / content-map 对八项结论一致（见第 6 节结论）
