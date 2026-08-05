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
- **默认覆盖与同一步多更新冲突必须分开**：默认覆盖 / last-value 语义 = 单个新值替换当前值（顺序执行中的普通字段更新）；同一步多更新 = 另一类问题（是否允许多值写入、如何合并）；**默认覆盖不是并行冲突解决机制**，不得写"自动取最后一个值""解决并发写冲突""没有 reducer 就能安全合并多个更新"
- **三方职责**：Node 产生业务结果与 State Update；Reducer 定义单个 channel 合并规则（可承载应用定义的数据合并语义：event append / numeric accumulation / set union / deduplication / map merge）；Graph Runtime 接收更新、**根据已编译的 State schema 查找并应用**该 channel 的更新规则、计算并写入新 State（不是每轮动态制定策略）；三个"不得写"（Node 不调用 Reducer、Reducer 不调度 Node、Reducer 不决定业务动作）
- **Overwrite 与 Append 无高低之分**：选择取决于 channel 数据契约；没有"list 字段天然自动追加"；**Append 只是一个示例**（Reducer 通用能力不限于序列拼接，不把 Reducer 等同 operator.add）
- **Reducer ≠ 业务决策器（不是绝对化"与业务无关"）**：可承载应用定义的数据合并语义，但职责限制在 channel 值的组合与归并；≠ Model Decision / Routing / Scheduler / Policy / Authorization / Lifecycle Guard / Conflict Resolution Policy（值组合归并 vs 权威性裁决）/ Transaction Manager；不负责：下一业务动作 / 权限与安全裁决 / 生命周期决策 / 外部事实权威性判断 / 业务版本冲突仲裁 / 调度执行顺序
- **纯函数是工程约束非框架自动保证（三层）**：定义 = current + incoming → next；工程推荐 = 确定性 / 纯函数化 / 无外部副作用 / 不原地改输入 / 可重复执行 / 可独立测试；框架事实 = Reducer 是应用提供的 callable，LangGraph 不自动保证无副作用（有副作用增加重放/并发/测试风险）；当前 Demo = operator.add 是简单值合并函数，不据此外推所有 reducer 天然纯净
- **默认更新证据三层**：代码证据（schema 未声明 reducer）/ 执行证据（最终字段断言与 Node update 一致）/ 范围（非并发专项测试）；不写"默认 overwrite 已被专项测试证明"
- **并发边界严格收窄**：为多更新合并提供语义基础；不宣称线程安全 / 事务隔离 / 确定性并发 / 所有 fan-out 合并 / 控制并发顺序；当前 Demo 无并发写同 channel 测试 → 明确"未验证"；**history 顺序证据收窄**：测试只验证顺序执行路径的追加顺序，未验证并行更新 history 的稳定顺序（operator.add 不等于并发业务顺序保证）
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
- [ ] PR #35 Architecture Review 七项修正全部应用（默认覆盖 vs 同一步多更新冲突 / Reducer 业务合并语义边界 / 纯函数工程约束 / 默认更新证据归属三层 / Graph Runtime 应用规则表述 / Append 范围 / history 顺序证据收窄）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #35 创建。
- 2026-08-05：**PR #35 Architecture Review 七项修正**（commit：docs: refine reducer update and concurrency boundaries）全部应用并推送更新 PR #35：
  1. **默认覆盖与同一步多更新冲突分离**：默认覆盖 / last-value = 单个新值替换当前值；同一步多更新是另一类问题；"默认覆盖不是并行冲突解决机制"；新增误区 #11（自动取最后一个值）——主线 / 12.1 / 12.2 / 12.4 / 12.9 / Q1-Q4 / Q7 / 总结 / 验收标准
  2. **Reducer 业务边界**：删除"与业务无关的机械规则"绝对化；"Reducer 不是业务决策器，可承载应用定义的数据合并语义（append / 累加 / set union / 去重 / map merge），职责限制在值的组合与归并"；不负责清单 6 项——12.2 / 12.3 / 12.7 / 12.8 / Q5 / 误区 #1
  3. **纯函数工程约束三层**：定义 / 工程推荐 / 框架事实（Reducer 是应用 callable，LangGraph 不自动保证无副作用）；当前 Demo 不据此外推——12.2 / 12.7 / 12.8 / 12.9 / 验收标准
  4. **默认更新证据归属三层**：代码（schema 未声明 reducer）/ 执行（最终字段断言）/ 范围（非并发专项）；不写"专项测试证明 overwrite"——12.10 / Q10
  5. **Graph Runtime 表述**："选择 channel 规则" → "根据已编译的 State schema 查找并应用"（非每轮动态制定）——Mermaid / 12.3 / 12.5 / 12.7 / Q3 / Q6
  6. **Append 只是一个示例**：Reducer 通用能力不限于序列拼接；不把 Reducer 等同 operator.add——12.2 / 12.4
  7. **history 顺序证据收窄**：测试验证的是顺序执行路径；并行 history 稳定顺序未验证；operator.add ≠ 并发业务顺序保证——12.4 / 12.9 / 12.10 / Q7 / Q10
