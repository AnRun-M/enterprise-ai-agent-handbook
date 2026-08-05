# TASK-0021：Chapter 14《Checkpoint——持久化与恢复》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 |
| Related Chapter | 第 1 章（Human Stop 暂停态）、第 2 章（State 快照引用）、第 7 章（Memory）、第 9 章（Graph State）、第 12 章（Reducer）、第 13 章（动态 work item）；TASK-0014（Part 03 规划，ch14 定位） |
| Related Example | examples/basic_langgraph（agent.py / graph.py：未启用 Checkpointer）、examples/checkpoint_hitl（预留） |
| Related Test | 无（Demo 未启用，如实标注；证据为 docstring / 官方核验记录） |

## 目标

编写 Part 03 第六个原语章 `docs/03-langgraph-core/ch14-checkpoint.md`：回答「图执行如何从"内存易失"变成"可恢复"？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Graph State 是执行中的当前状态；Checkpoint 是图在某个执行时刻持久化的状态与执行上下文快照。Checkpointer 负责保存和读取这些快照，使 Runtime 能够恢复、重放或继续执行；Checkpoint 不是 Memory，也不等于一个简单的 State 字典副本。

**三条核心边界（必须守住）**：① Graph State = 当前执行状态；Checkpoint = 执行时刻快照；② Checkpointer 负责保存 / 读取，但恢复策略、重放语义、续跑规则由 Runtime 与应用契约共同决定；③ Checkpoint 不是 Memory、不等于简单 State 字典副本。

## 需要新增

- `docs/03-langgraph-core/ch14-checkpoint.md`（14.1-14.11 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0021-chapter-14-checkpoint.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 14 章）
- `docs/03-langgraph-core/index.md`（第 14 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 14 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 14 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线与三条边界固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch02 State 快照边界 / ch07 Memory / architecture-map 第五节），再讲 Checkpoint 承载；禁止从 API 出发解释概念
- **Checkpointer / persistence layer 职责**：写入 / 读取 checkpoint、按 thread-标识组织检索、列举 history、保存恢复所需 pending writes、序列化反序列化；恢复策略 / 重放语义 / 续跑规则 / 治理策略 = Runtime 与应用契约共同决定（不展开 BaseCheckpointSaver 方法名 / 存储表结构 / SQLite-Postgres API / serializer 代码）
- **持久化内容（StateSnapshot 语义，面向读者）**：State channel values（**reducer 合并结果通常已体现在 channel values 中**，history 累计在 values["history"]——不写成必然独立的第二份业务数据）+ next / 下一执行位置 + checkpoint / thread config 与标识 + metadata + parent checkpoint relationship + tasks / interrupts 等执行任务信息；底层内部信息（channel versions / pending writes / serializer 数据）不展开；**pending writes ≠ 完整 StateSnapshot**（完整 checkpoint 通常对应 superstep 边界）
- **Checkpoint ≠ Memory（桥接官方术语）**：本书语义 = 快照 vs 经过选择治理的跨执行信息（第 7 章区分轴）；**官方术语桥接**：thread 内 Checkpointer 保留状态可被称为 short-term memory（同一 thread 跨多次 invoke 保留；Store = cross-thread long-term）——本书仍归入 Checkpoint / thread state persistence；不得绝对化"Checkpoint 只存在于一次 invoke / 只有 Memory 才能跨 invocation / Checkpointer 不可能提供 memory 语义"
- **Recovery / Replay / Resume 精确区分**：Recovery = 故障后恢复持久化状态和执行上下文（**不简单等于全部节点重跑**，pending writes 可能避免重跑，未验证）；Replay = 从历史 checkpoint 重跑其后步骤（之前跳过，LLM / Tool / API / Interrupt 可能再次触发，非播放历史输出，副作用幂等属 Part 05）；Resume = 从中断状态继续（可携带新的人工输入或控制结果，Interrupt / Command 机制留 ch15）
- **无 Checkpointer 边界**：未启用时 Graph Runtime 不自动维护可恢复 thread checkpoint history；应用仍可获得最终 State 并可自行持久化业务结果——但仅保存最终字段值 ≠ 拥有恢复位置 / 历史快照 / pending writes / 重放与续跑协议
- **版本化与形成时点**：历史 checkpoint 固定；update_state 或后续运行创建新 checkpoint、不原地修改旧 checkpoint、fork / replay 派生新轨迹；完整 checkpoint 通常对应 superstep 边界，节点级 pending writes 可更早持久化但不等于完整 checkpoint（不展开 Pregel 内部算法）
- **Checkpoint 与 Interrupt**：承载基础关系（第 15 章依赖），本章只立边界
- **当前 Demo 未启用**：如实标注教学边界（graph.py 无 checkpointer / agent.py docstring / examples/checkpoint_hitl 预留 / references 核验记录 / architecture-map 未决项）
- **不提前展开**：Checkpointer API 写法与存储后端（框架 API 教程 / 实现细节）、生产恢复语义（HITL / 幂等 / 补偿 / 审计——Part 05）、Interrupt API（ch15）、Stream（ch16）、Subgraph（ch17）
- **证据诚实**：仓库无 Checkpoint 实现证据——基于 docstring / graph.py / 预留目录 / 官方核验记录；未验证清单如实标注（保存读取行为 / 崩溃恢复确定性 / 重放语义 / 续跑规则 / reducer 累积序列化 / 并发组合 / 生产恢复策略）；不推断实现行为
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-13、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 14.1-14.11 完成，Q1-Q10 全部回答
- [ ] 固定主线与三条核心边界逐字保持
- [ ] 5 张 Mermaid 图（执行流 + 快照时刻 / Graph State vs Checkpoint vs Memory 边界 / Checkpointer 保存读取与 Runtime 契约 / 持久化内容 / 恢复-重放-续跑）——图不暗示 Checkpointer 决定恢复策略
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0021 Status = in_progress；ROADMAP Chapter 14 = draft / 待架构审查；content-map 第 14 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-14-checkpoint，commit `docs: draft chapter 14 checkpoint`）
- [ ] PR #39 Architecture Review 七项修正全部应用（持久化内容 StateSnapshot / Memory 术语桥接 / Checkpointer 机制职责 / Recovery-Replay-Resume 精确区分 / 无 Checkpointer 边界 / 版本化边界 / superstep-pending writes 边界）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #39 创建。
- 2026-08-05：**PR #39 Architecture Review 七项修正**（commit：docs: refine checkpoint persistence and memory boundaries）全部应用并推送更新 PR #39：
  1. **持久化内容改 StateSnapshot 语义**（14.2 / 14.5 / Mermaid / Q2 / Q6 / 误区 / 验收标准）：channel values（reducer 合并结果通常已体现在其中，history 累计在 values["history"]——不写成独立第二份业务数据）+ next 执行位置 + thread config 与标识 + metadata + parent relationship + tasks / interrupts 信息；底层内部信息（channel versions / pending writes / serializer 数据）不展开
  2. **Checkpoint / Memory 官方术语桥接**（14.8 / Q8 / 误区 #2/#8 / 总结 / 验收标准）：thread 内 Checkpointer 保留状态 = 官方 short-term memory（同一 thread 跨 invoke；Store = cross-thread long-term）；本书仍归入 Checkpoint / thread state persistence；删除"只存在于一次 invoke / 只有 Memory 跨 invocation / Checkpointer 不可能提供 memory 语义"绝对化
  3. **Checkpointer 机制职责扩展**（14.3 / Mermaid / Q4 / 误区 / 验收标准）：写入 / 读取 / thread-标识组织检索 / 列举 history / 保存 pending writes / 序列化反序列化 vs Runtime-应用契约（恢复点 / replay-resume 入口 / 副作用幂等 / 合并新输入 / 治理 / 审批权限）；不展开 BaseCheckpointSaver / 表结构 / SQLite-Postgres / serializer 代码
  4. **Recovery / Replay / Resume 精确区分**（14.4 / Q5 / 14.9 / 误区 #5/#9 / 总结 / 验收标准）：Recovery 不简单等于全部节点重跑（pending writes 可能避免重跑，未验证）；Replay 跳过 checkpoint 之前、LLM / Tool 再次触发、非播放历史输出、幂等属 Part 05；Resume 可携带新输入、Interrupt / Command 留 ch15
  5. **无 Checkpointer 边界修正**（14.1 / Q1 / 14.6 / 误区）：未启用时应用仍可获得最终 State 并可自行持久化业务结果；仅保存最终字段值 ≠ 拥有恢复位置 / 历史快照 / pending writes / 重放与续跑协议
  6. **版本化边界**（14.2 / 误区）：历史 checkpoint 固定；update_state 或后续运行创建新 checkpoint、不原地修改旧 checkpoint、fork / replay 派生新轨迹（time-travel 细节不展开）
  7. **superstep / pending writes 边界**（14.1 / 14.2 / 14.5 / Q2 / Q6）：完整 checkpoint 通常对应 superstep 边界；节点级 pending writes 可更早持久化但不等于完整 checkpoint（不展开 Pregel 内部算法）
