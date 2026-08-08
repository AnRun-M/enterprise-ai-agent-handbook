# TASK-0028：Chapter 18《StateGraph 构图与 Graph Runtime 执行模型》（Part 04 前置章）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-08 |
| Updated | 2026-08-08 |
| Related ADR | ADR-0001 / ADR-0002 / ADR-0003 |
| Related Chapter | 第 9-17 章（Part 03 语义，只引用）；TASK-0026（Part 04 Scope Planning，冻结决策） |
| Related Example | examples/basic_langgraph（graph.py / agent.py——真实代码直接证据） |
| Related Test | tests/basic_langgraph（`test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 04 前置章 `docs/04-text2sql/ch18-stategraph-graph-runtime.md`：回答「Part 03 已建立的 Runtime 语义如何被组装成一个可执行 Graph？」。**核心主线固定（用户 2026-08-08 冻结，写作不得偏离）**：StateGraph 负责声明图结构，compile() 将图定义转换为可执行的 Graph Runtime，invoke()/stream() 通过该 Runtime 驱动 State、Node 与控制流运行；这些 API 不重新定义 Part 03 的 Runtime 语义，只负责把既有语义组装并执行。

**章节结构冻结（用户建议）**：按链式组织——**定义图 → 注册组件 → 连接控制流 → compile → invoke/stream → 与 Part 03 对照**；**不按 StateGraph.add_node/add_edge/... 方法列表排目录**（守住 Runtime-first）。

**只集中讲四件事**：① 构图入口 ② 组件注册与连接 ③ compile() 的语义边界 ④ 编译后 Runtime 的执行入口。Node / Edge / Reducer / Command / Send / Checkpoint / Interrupt / Stream 只引用 Part 03，不重新解释。

## 需要新增

- `docs/04-text2sql/ch18-stategraph-graph-runtime.md`（18.1-18.10 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0028-chapter-18-stategraph-graph-runtime.md`（本文件）

## 需要修改

- `mkdocs.yml`（Text-to-SQL 导航加入第 18 章）
- `docs/04-text2sql/index.md`（第 18 章条目）
- `docs/00-introduction/content-map.md`（新增第 18 章行，状态「实现完成 / 待架构审查」；Part 4 行更新）
- `ROADMAP.md`（v0.5.0 Chapter 18 → draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线与章节结构冻结**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：每步先引用 Part 03 语义（ch09-17），再讲组装/执行承载；禁止从 API 方法列表出发
- **只引用不重新解释**：Node（ch10）/ Edge（ch11）/ Reducer（ch12）/ Command-Send（ch13）/ Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17）——语义解释一律回指
- **compile() 语义边界**：声明 → 可执行 Runtime 的转换；不是新语义、不是业务规则、不执行图
- **invoke / stream**：编译后 Runtime 的执行入口（invoke = 最终结果；stream = 过程视图，引用 ch16）
- **证据优势**：本章有真实代码直接证据（graph.py / agent.py）——构图 / 注册 / 连接 / compile / invoke 全部可引用；未验证清单如实标注（Runtime 内部调度 / stream 行为 / Checkpoint-interrupt 组合 / API 参数面）
- **不提前展开**：T01-T12 业务重构（后续章节）、StateGraph API 完整参数面（API 教程超出范围）、Pregel 内部实现（超出本书范围）
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014 / TASK-0026、Chapter 08-17 正文、examples、tests、principles、ADR、references、architecture-map、Part 编号

## 验收标准

- [ ] 章节结构 18.1-18.10 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持；链式结构（定义图 → 注册 → 连接 → compile → invoke/stream → 对照）非方法列表
- [ ] 5 张 Mermaid 图（语义→组装→执行 / 链式流程 / compile 语义边界 / invoke-stream 执行入口 / 与 Part 03 对照）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0028 Status = in_progress；ROADMAP Chapter 18 = draft / 待架构审查；content-map 第 18 章 = 实现完成 / 待架构审查
- [ ] PR 创建（分支 feature/chapter-18-stategraph-graph-runtime，commit `docs: draft chapter 18 stategraph graph runtime`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-08：任务创建，正文初稿完成（待补）
