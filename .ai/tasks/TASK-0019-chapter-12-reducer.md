# TASK-0019：Chapter 12《Reducer——状态合并语义》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | 第 2 章（Execution State）、第 9 章（Graph State）、第 10 章（Execution Nodes）、第 11 章（Edge）；TASK-0014（Part 03 规划，ch12 定位句） |
| Related Example | examples/basic_langgraph（state.py / nodes.py / graph.py） |
| Related Test | tests/basic_langgraph（`test_history_reducer_appends_without_duplicates` / `test_reducer_semantics_operator_add` / `test_direct_equivalence_with_manual` 等） |

## 目标

编写 Part 03 第四个原语章 `docs/03-langgraph-core/ch12-reducer.md`：回答「Node 返回 State Update 后，Graph Runtime 如何得到新的 Graph State？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Node 返回 State Update；Reducer 定义同一 State channel 收到更新时如何合并；Graph Runtime 应用该合并规则，形成新的 State。Reducer 是数据合并规则，不是业务决策器、不是路由器、不是 Scheduler、不是权限系统、不是生命周期守卫、也不是并发控制器。当前 Demo：history 使用追加语义；其他字段使用默认覆盖语义。

## 需要新增

- `docs/03-langgraph-core/ch12-reducer.md`（12.1-12.12 结构，回答 Q1-Q10，6 张 Mermaid 图）
- `.ai/tasks/TASK-0019-chapter-12-reducer.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 12 章）
- `docs/03-langgraph-core/index.md`（第 12 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 12 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 12 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 语义（ch02 State 更新机制 / ch09 schema 与 channel / ch10 State Update），再讲 LangGraph 承载；禁止从 API 出发解释概念
- **三方职责**：Node 产生业务结果与 State Update；Reducer 定义单个 channel 合并规则；Graph Runtime 接收更新、选规则、计算并写入新 State；三个"不得写"（Node 不调用 Reducer、Reducer 不调度 Node、Reducer 不决定业务动作）
- **Overwrite 与 Append 无高低之分**：选择取决于 channel 数据契约；没有"list 字段天然自动追加"
- **Reducer ≠ 业务逻辑**：≠ Model Decision / Routing / Scheduler / Policy / Authorization / Lifecycle Guard / Conflict Resolution Policy（机械合并 vs 权威性裁决）/ Transaction Manager
- **并发边界严格收窄**：为多更新合并提供语义基础；不宣称线程安全 / 事务隔离 / 确定性并发 / 所有 fan-out 合并 / 控制并发顺序；当前 Demo 无并发写同 channel 测试 → 明确"未验证"
- **Annotated / operator.add 表述**：Annotated 是声明 reducer 挂载关系的一种 Python 表达方式（不是 Reducer 本身）；operator.add 不是唯一追加实现；如实引用 `state.py` 真实代码
- **不提前展开**：Annotated API 细节 / 自定义 Reducer 写法 / Pregel / Channel 内部实现 / Command / Send（ch13）/ Checkpoint（ch14）/ Interrupt（ch15）/ Stream（ch16）/ Subgraph（ch17）
- **不引入 LangChain API**（一句边界：LangChain 不属于本章）；不重新定义 Part 02 语义
- 证据以仓库真实代码与测试为准（state.py / nodes.py / tests）；已核实：history = `Annotated[list[StepEvent], operator.add]`、其余字段默认覆盖、Node 返回增量、无并发写测试、无自定义 Reducer、无 Pregel 使用——任务书与代码一致，无差异
- 测试数量以最新 CI 为准不写死；未验证清单如实标注
- 不修改 TASK-0014、Chapter 08/09/10/11、examples、tests、principles、ADR、architecture-map、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 12.1-12.12 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持
- [ ] 6 张 Mermaid 图（Node→Update→Reducer→Merged State / Current+Incoming→Next / Overwrite vs Append / channels 与不同 reducer / 三方职责 / Reducer 与业务冲突裁决边界）——图不暗示 Reducer 调度 Node、调用 Tool、做业务判断、控制线程
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0019 Status = in_progress；ROADMAP Chapter 12 = draft / 待架构审查；content-map 第 12 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-12-reducer，commit `docs: draft chapter 12 reducer`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
