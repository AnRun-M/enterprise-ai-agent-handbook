# TASK-0020：Chapter 13《Command 与 Send——动态控制流》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 |
| Related Chapter | 第 6 章（Scheduler / work item）、第 10 章（Node）、第 11 章（Conditional Edge）、第 12 章（Reducer）；TASK-0014（Part 03 规划，ch13 定位） |
| Related Example | examples/basic_langgraph（README 第 9 节：未使用的 LangGraph 能力） |
| Related Test | 无（Demo 未使用 Command / Send，如实标注） |

## 目标

编写 Part 03 第五个原语章 `docs/03-langgraph-core/ch13-command-send.md`：回答「Conditional Edge 之外的动态控制流需求如何表达？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Conditional Edge 根据图外定义的 routing callable 选择路径；Command 允许 Node 的返回结果同时携带 State Update 与路由意图；Send 根据运行时数据动态创建多个 work item，实现 fan-out。Command 与 Send 都属于动态控制流原语，但一个解决"更新与导航绑定"，另一个解决"按数据动态展开并行工作"。

**两条硬边界（用户强调）**：不要把 Command 与 Send 混成同一个原语；不要把 Send 简化成普通 Conditional Edge。

## 需要新增

- `docs/03-langgraph-core/ch13-command-send.md`（13.1-13.11 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0020-chapter-13-command-send.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 13 章）
- `docs/03-langgraph-core/index.md`（第 13 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 13 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 13 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标）与**两条硬边界**，不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch06 work item 调度 / Scheduler 职责）与 Part 03 已建立语义（ch10 Node / ch11 Conditional Edge / ch12 Reducer），再讲 Command / Send 承载；禁止从 API 出发解释概念
- **Command**：节点返回结果同时携带 State Update 与路由意图；与「先更新 State 再路由」的区别 = 表达位置变化、解释权不变（Graph Runtime）；Command 的部分更新走同一 channel 合并（ch12）
- **Send**：按运行时数据动态创建多个 work item（fan-out / map-reduce）；≠ Conditional Edge（选一条路 vs 按数据展开多个执行单元）；work item 的产生 ≠ 调度执行（调度在 Scheduler / Graph Runtime）
- **不混同 Command 与 Send**：问题不同（更新与导航绑定 vs 按数据展开并行）、作用对象不同（节点结果形态 vs 执行单元产生方式）；可组合但先分清各自问题
- **证据诚实**：仓库无 Command / Send 实现证据——基于 `references/official/langgraph.md` 核验记录（刻意未使用）与 README 第 9 节；未验证清单如实标注（行为语义 / fan-out 合并 / 与静态路由等价性 / 动态生命周期 / Checkpoint-Interrupt 组合）；不推断实现行为
- **不提前展开**：Command / Send API 签名与写法（框架 API 教程超出范围）、Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17，仅引用 map-reduce 组合方向）、生产重试 / 幂等 / 补偿（Part 05）
- **不引入 LangChain API**（一句边界）；不重新定义 Scheduler / Node / Reducer 语义
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-12、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 13.1-13.11 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持；Command / Send 不混同、Send 不简化成 Conditional Edge
- [ ] 5 张 Mermaid 图（静态路由 → 两类动态需求 / Command：State Update + 路由意图 → Graph Runtime / Send：数据 → work items → fan-out → 归并 / Command vs Send 对比 / 当前 Demo 静态图反例）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0020 Status = in_progress；ROADMAP Chapter 13 = draft / 待架构审查；content-map 第 13 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-13-command-send，commit `docs: draft chapter 13 command and send`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
