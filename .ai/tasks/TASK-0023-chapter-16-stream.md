# TASK-0023：Chapter 16《Stream——流式输出》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-06 |
| Updated | 2026-08-06 |
| Related ADR | ADR-0001 / ADR-0003 |
| Related Chapter | 第 2 章（history）、第 8 章（集成点）、第 11 章（路由）、第 12 章（Reducer / history）、第 14 章（Checkpoint）、第 15 章（Interrupt，正交）；TASK-0014（Part 03 规划，ch16 定位） |
| Related Example | examples/basic_langgraph（agent.py：仅同步 invoke） |
| Related Test | 无（Demo 未使用，如实标注；证据为同步 invoke 代码事实 / 官方核验记录） |

## 目标

编写 Part 03 第八个原语章 `docs/03-langgraph-core/ch16-stream.md`：回答「调用方如何在图仍在执行时持续接收运行进展与增量输出？」。**核心主线固定（用户 2026-08-06 指定，2026-08-07 合并前清理统一为最终表述，写作不得偏离）**：Stream 让调用方在图仍在执行时持续接收运行进展与增量输出；它是多类执行事件的统一观察和交付协议，不决定路由、不修改业务状态，也不等于完整的日志系统。Graph Runtime 汇聚执行过程中由 Node、Tool、模型调用及 Runtime 子系统产生的数据，并依据 Stream Mode 封装和交付流事件；应用选择消费模式和展示方式，背压是应用、Graph Runtime 与传输层共同形成的交付契约；Stream 与 Interrupt 正交，一个解决"边跑边看"，一个解决"暂停后再继续"。

## 需要新增

- `docs/03-langgraph-core/ch16-stream.md`（16.1-16.9 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0023-chapter-16-stream.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 16 章）
- `docs/03-langgraph-core/index.md`（第 16 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 16 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 16 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 / Part 03 已建立语义（ch02 history / ch11 路由 / ch12 Reducer / ch15 Interrupt），再讲 Stream 承载；禁止从 API 出发解释概念
- **token streaming 两层边界**：token / message chunk 的生成来自模型调用（模型来源）；LangGraph 可通过 messages 流模式**在图执行层交付这些增量并附带节点与调用元数据**（图 Runtime 交付，可从 Node / Tool / Subgraph / Task 内模型调用产生）；不展开供应商 API 或具体调用参数
- **四类流事件**：State projection（values / updates）/ Model output（messages / chunks + metadata）/ Application event（custom，Node-Tool 主动发送）/ Runtime event（checkpoints / tasks / debug）；"Stream 是多类执行事件的统一流式交付协议，不只是 State 增量流"
- **流事件生产职责**：Node / Tool 返回 State Update 并可产生 custom progress event；Model call 产生 chunks；Checkpointer / task runtime 产生 checkpoint-task 信息；**Graph Runtime 汇聚并依据 Stream Mode 封装和交付**（标记 event type / namespace / metadata）；不展开 get_stream_writer API
- **Stream / Observability 边界（不互斥）**：Streaming protocol = 事件如何实时交付；Observability system = 采集 / 关联 / 持久化 / 检索 / 分析 / 告警；debug-tasks-checkpoints 流模式可携带可观测信息、Stream 可成为数据入口，但 **Stream 本身 ≠ 完整日志 / Trace / Metric 系统**（不自动提供存储 / 查询 / 聚合 / 告警）
- **最终 State 与流事件两类**：State-related modes（values / updates，成功终止时提供最终 State 的演进投影）；Non-state modes（messages / custom / tasks / checkpoints / debug，不必写入最终 State）；**任意流事件 ≠ State Update；仅凭任意 Stream Mode 不一定能重建最终 State**（取决于 values-updates 完整性、Reducer 语义与事件缺失）；暂停 / 失败 / 取消 / 提前终止不能假设完整最终 State；仓库未验证一致性
- **背压分层**：Application consumer（选模式 / 消费速度 / 过滤展示 / 主动取消）→ Graph streaming runtime（迭代与交付语义 / 内部缓冲与取消传播）→ Transport / server（SSE / WebSocket / HTTP buffering / 超时流控）→ Production policy（丢弃 / 限流 / 慢消费者治理 / 配额，Part 05）；"应用选择消费模式和展示方式；背压是应用、Graph Runtime 与传输层共同形成的交付契约"
- **与 Interrupt 正交**：边跑边看（不暂停、不改变执行）vs 暂停后再继续；可共存、互不依赖；Interrupt payload / interrupted 状态可通过流式协议暴露给调用方，但不合并语义
- **三条硬边界**：不决定路由（观察协议，路由属 ch11）；不修改业务状态（只读观察 + 交付，State 更新仍走 Node Update + Graph Runtime 合并）；不等于完整日志系统（可承载可观测事件 ≠ 完整 Observability）
- **不提前展开**：astream / astream_events API 写法（框架 API 教程）、生产流式交付（SSE / WebSocket / 部分输出策略 / 前端呈现——Part 05）、流式下 HITL 交互（Part 05）、Subgraph 嵌套流（ch17，仅引用）
- **当前 Demo 未使用**：如实标注（agent.py 仅同步 invoke / references 核验记录 / architecture-map 概念坐标）
- **证据诚实**：仓库无 Stream 实现证据——基于同步 invoke 代码事实与官方核验记录；未验证清单 6 项如实标注；不推断实现行为
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-15、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 16.1-16.9 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持
- [ ] 5 张 Mermaid 图（同步 invoke vs 流式 / 流事件类型与最终 State / Stream 三条硬边界 / 消费模式与背压（应用契约）/ Stream 与 Interrupt 正交）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0023 Status = in_progress；ROADMAP Chapter 16 = draft / 待架构审查；content-map 第 16 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-16-stream，commit `docs: draft chapter 16 stream`）
- [x] PR #43 Architecture Review 七项修正全部应用（token streaming 两层边界 / 四类流事件 / 生产职责汇聚 / Stream-Observability 不互斥 / 最终 State 两类关系 / 背压分层 / Stream-Interrupt 组合边界）
- [x] PR #43 合并前一致性清理全部应用（本章边界 token 旧结论统一 / 验收标准固定主线同步 / PR 顶部摘要直接更新）
- [x] PR #43 复审通过并 squash merge 到 main（commit 94ff6e1，CI build/test 双绿，2026-08-07）→ Chapter 16 最终完成
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-06：任务创建，正文初稿完成；四源更新；PR #43 创建。
- 2026-08-06：**PR #43 Architecture Review 七项修正**（commit：docs: refine stream modes and delivery boundaries）全部应用并推送更新 PR #43：
  1. **token streaming 两层边界**（章节顶部 / 16.3 / 误区 #9 / Q3）：token / message chunk 生成来自模型调用；LangGraph 通过 messages 流模式在图执行层交付增量并附节点与调用元数据；删除"token 流不属于图执行层"绝对化
  2. **四类流事件**（16.1 Mermaid / 16.3 / Q3 / 16.7 / 误区 / 总结 / 验收标准）：State projection / Model output / Application event / Runtime event；"统一流式交付协议，不只是 State 增量流"
  3. **流事件生产职责**（固定主线 / 16.2 / 16.3 / 16.4 / 总结）：Graph Runtime 汇聚（Node-Tool / Model call / Checkpointer-task runtime 产生）并依据 Stream Mode 封装交付（event type / namespace / metadata）；不展开 get_stream_writer
  4. **Stream / Observability 不互斥**（16.2 / 16.5 / Mermaid / Q6 / 误区 #3）：Streaming = 实时交付；Observability = 采集关联持久化检索分析告警；debug-tasks-checkpoints 可携带可观测信息、Stream 可成为入口，但 ≠ 完整日志系统（无存储查询聚合告警）
  5. **最终 State 两类关系**（16.3 / Mermaid / Q3 / Q10 / 误区 #4）：State-related modes 提供成功终止时演进投影；Non-state modes 不必写入最终 State；任意流事件 ≠ State Update、不一定能重建最终 State；暂停失败取消提前终止不能假设完整最终 State
  6. **背压分层**（固定主线 / 16.4 / 消费模式表 / Mermaid / Q7 / 误区 #10）：Application consumer → Graph streaming runtime → Transport / server → Production policy（Part 05）；"背压是应用、Graph Runtime 与传输层共同形成的交付契约"
  7. **Stream / Interrupt 组合边界**（16.4）：保留正交；Interrupt payload / interrupted 状态可通过流式协议暴露，但不合并语义（不展开 ch15 API）
- 2026-08-07：**PR #43 合并前一致性清理**（commit：docs: align stream summary and token delivery terminology）：本章边界"token 级流（LLM 内部）——不属于图执行层"统一为"token / message chunk 由模型调用产生；LangGraph 可以通过 messages 流模式在图执行层交付这些增量，并附带节点与调用元数据——本章不展开模型供应商 API 或具体参数"；验收标准固定主线同步（Graph Runtime 汇聚并按 Stream Mode 封装交付 / 背压分层契约）；PR #43 描述顶部直接更新（固定主线 / Q3 / Q6 / Q7 / Q10 / 关键边界 / Mermaid / Review Focus，删除 5 项旧口径）。
- 2026-08-07：PR #43 经 Architecture Review 复审通过，squash merge 到 main（commit 94ff6e1，CI build/test 双绿）→ **TASK-0023 标记 completed；Chapter 16 最终完成**；本 Memory PR（docs/post-pr43-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
