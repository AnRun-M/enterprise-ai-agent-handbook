# TASK-0024：Chapter 17《Subgraph——图组合与复用》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-07 |
| Updated | 2026-08-07 |
| Related ADR | ADR-0001 / ADR-0003 |
| Related Chapter | 第 0 章（Agent 五要素）、第 6 章（模块化编排 / 子流程复用）、第 8 章（执行结构可审查）、第 9 章（Graph State / schema 契约）、第 10 章（Node）、第 13 章（Send map-reduce）、第 16 章（嵌套流事件）；TASK-0014（Part 03 规划，ch17 定位） |
| Related Example | examples/basic_langgraph（README 第 19 节：校验-修复回路抽子图 = 扩展方向） |
| Related Test | 无（Demo 未使用，如实标注；证据为官方核验记录 / 扩展方向声明） |

## 目标

编写 Part 03 收官章 `docs/03-langgraph-core/ch17-subgraph.md`：回答「复杂 Agent 如何通过图组合实现模块化与复用？」。**核心主线固定（用户 2026-08-07 指定，写作不得偏离）**：Subgraph 将一组 Node、State channels 与控制流封装为可组合的图级执行单元。父图负责调用与整体编排，子图维护自身内部执行结构；父子图如何交换 State，取决于共享 schema、输入输出映射与显式适配契约。Subgraph 不是普通 Node 的同义词，也不是微服务或独立 Agent 的必然边界。

**Part 03 收官边界（用户提醒）**：Chapter 17 是 Part 03 收官章，但正文完成并合并后**仍应单独执行一次 Part 03 Scope Closure / 收官检查**——**不得**在 Chapter 17 正文 PR 或 Memory PR 中直接把 Part 03 标记为最终完成。

## 需要新增

- `docs/03-langgraph-core/ch17-subgraph.md`（17.1-17.10 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0024-chapter-17-subgraph.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 17 章）
- `docs/03-langgraph-core/index.md`（第 17 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 17 章行，状态「实现完成 / 待架构审查」；Part 3 行更新——**不标 Part 03 最终完成**）
- `ROADMAP.md`（v0.4.0 新增 Chapter 17 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标）与 **Part 03 收官边界**，不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 / Part 03 已建立语义（ch06 模块化编排 / ch09 schema 契约 / ch10 Node / ch13 Send / ch16 嵌套流），再讲 Subgraph 承载；禁止从 API 出发解释概念
- **Subgraph = Graph Composition，不是大 Node（固定表述，17.2）**："Subgraph 不是 Node 的增强版，而是 Graph 的组合（composition）——父图看到的是一个图级执行单元，而不是一个特殊 Node"；更准确：Subgraph 是 Graph 作为一个可组合执行单元被父 Graph 注册和调用——不是"Node 变复杂"，而是"Graph 被组合"；层级不是 Node → Subgraph → Graph
- **Parent Graph 不拥有 Child Graph（17.3）**：父图描述调用关系，不是拥有 Child 生命周期；生命周期与调度由 Runtime 负责（ch10 / ch11 / ch13 一贯原则）
- **Subgraph 不产生新的 Runtime（17.3）**：同一 Runtime 中的图组合语义；不讨论 RemoteGraph / A2A / Multi Runtime
- **State Exchange 是执行契约（17.4）**：父图与子图交换的是 execution contract，State mapping 只是其中一种表达方式；真正重要的是 Execution Boundary（子图是独立执行边界）；不要把 Subgraph 理解为 DTO Mapping
- **与 Send 不同层次（17.5）**：Send → 多个 Work Item → 可以进入同一个 Subgraph；不是 Send 创建 Subgraph、也不是 Subgraph 实现 Send；固定表述"Send 负责描述动态 work items，Subgraph 负责组织单个 work item 内部执行结构，两者解决不同层次的问题，可组合但互不替代"
- **当前 Demo 未使用 = 没有组合需求（17.7）**：没有出现值得独立封装并复用的一组图结构，保持单图即可——不是能力缺失
- **父子 State 交换**：取决于共享 schema / 输入输出映射 / 显式适配契约——不是自动全量共享；子图内部字段不必全部暴露（ch09 可见范围语义）；字段语义仍走 ch09 / ch12
- **Subgraph ≠ 微服务 / ≠ 独立 Agent**：进程内结构组合 vs 部署通信边界；控制流组合单元 vs 拥有自己 Loop / 决策权 / 能力的执行主体（第 0 章五要素）；跨 Agent 协作（A2A）属 Part 06
- **与 Checkpoint / Interrupt / Stream 组合仅引用**（ch14-16）；**拆 / 不拆判据**：复用、可读性、可测试性（ch13 13.6 判据延续）
- **不提前展开**：Subgraph API 写法（框架 API 教程）、A2A（Part 06）、MCP 接入（Part 06）、生产级流程引擎（Part 04 / 05）、RemoteGraph / Multi Runtime（超出范围）
- **Part 03 Ending（17.10 收官句）**：Part 03 从 Graph State、Execution Node、Edge、Reducer、Command、Checkpoint、Interrupt、Stream 一直到 Subgraph，逐步建立了 Graph Runtime 的执行模型；下一部分将进入 StateGraph API 与框架实现层，而不是重新定义这些运行时概念
- **证据诚实**：仓库无 Subgraph 实现证据——基于官方核验记录与扩展方向声明；未验证清单 7 项如实标注；不推断实现行为（不因官方 examples 写成"已验证"）
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-16、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号；**不把 Part 03 标为最终完成**

## 验收标准

- [ ] 章节结构 17.1-17.10 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持；Part 03 收官边界遵守（正文与 Memory PR 不标记 Part 03 最终完成）
- [ ] 5 张 Mermaid 图（父图调用子图 / 子图内部结构封装 / 父子 State 交换契约 / Subgraph 与 Send map-reduce 组合 / Subgraph 边界（≠ Node / ≠ 微服务 / ≠ 独立 Agent））
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0024 Status = in_progress；ROADMAP Chapter 17 = draft / 待架构审查；content-map 第 17 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-17-subgraph，commit `docs: draft chapter 17 subgraph`）
- [x] PR #45 Architecture Review（REQUEST CHANGES）八项修正全部应用（Graph Composition 固定表述 / Parent 不拥有 Child / State Exchange 是执行契约 / 不产生新 Runtime / Send 不同层次 / Demo 未使用 = 无组合需求 / Evidence 保持 / Part 03 Ending）
- [x] PR #45 复审 APPROVED 并 squash merge 到 main（commit d7befd3，CI build/test 双绿，2026-08-07）→ Chapter 17 最终完成
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-07：任务创建，正文初稿完成；四源更新；PR #45 创建。
- 2026-08-07：**PR #45 Architecture Review（REQUEST CHANGES，八项）**（commit：docs: refine subgraph composition and runtime boundaries）全部应用并推送更新 PR #45：
  1. **Subgraph = Graph Composition，不是大 Node**（17.2 固定表述）："Subgraph 不是 Node 的增强版，而是 Graph 的组合（composition）——父图看到的是一个图级执行单元，而不是一个特殊 Node"；层级不是 Node → Subgraph → Graph，而是 Graph 被 Graph 组合
  2. **Parent Graph 不拥有 Child Graph**（17.3）：父图描述调用关系，不拥有 Child 生命周期；生命周期与调度由 Runtime 负责（ch10 / ch11 / ch13 一贯原则）
  3. **State Exchange 是执行契约**（17.4）：execution contract，mapping 只是表达方式之一；真正重要的是 Execution Boundary；不把 Subgraph 理解为 DTO Mapping
  4. **Subgraph 不产生新的 Runtime**（17.3）：同一 Runtime 中的图组合语义；不讨论 RemoteGraph / A2A / Multi Runtime
  5. **Send 与 Subgraph 不同层次**（17.5）：Send → 多个 Work Item → 可进入同一个 Subgraph；固定表述"可组合但互不替代"；不是 Send 创建 Subgraph、也不是 Subgraph 实现 Send
  6. **当前 Demo 未使用 = 没有组合需求**（17.7）：没有出现值得独立封装并复用的一组图结构，保持单图即可——不是能力缺失
  7. **Evidence 保持**（17.8）：继续"Repository 无 Subgraph → Reference 有 → 只能介绍边界不介绍实现"；不因官方 examples 写"已验证"
  8. **Part 03 Ending**（17.10 收官句）：Part 03 从 Graph State 到 Subgraph 逐步建立 Graph Runtime 执行模型；下一部分进入 StateGraph API 与框架实现层，不重新定义运行时概念
- 2026-08-07：PR #45 经 Architecture Review 复审 APPROVED，squash merge 到 main（commit d7befd3，CI build/test 双绿）→ **TASK-0024 标记 completed；Chapter 17 最终完成**；本 Memory PR（docs/post-pr45-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
- **Future maintenance**：None（本任务无遗留 maintenance 项；Part 03 Scope Closure / 收官检查将作为独立流程在 Memory PR 合并后单独执行）。
