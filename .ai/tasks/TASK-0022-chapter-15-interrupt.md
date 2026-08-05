# TASK-0022：Chapter 15《Interrupt——暂停与人工介入》

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | 第 1 章（Human Stop 暂停态）、第 9 章（END 哨兵）、第 10 章（异常 / 错误边界）、第 13 章（Command 作用域）、第 14 章（Checkpoint 承载）；TASK-0014（Part 03 规划，ch15 定位） |
| Related Example | examples/basic_langgraph（README 第 18 节：HITL 属 v0.4.0 / v0.6.0 里程碑）、examples/checkpoint_hitl（预留） |
| Related Test | 无（Demo 未使用，如实标注；证据为第 1 章声明 / 官方核验记录） |

## 目标

编写 Part 03 第七个原语章 `docs/03-langgraph-core/ch15-interrupt.md`：回答「图执行如何在可恢复执行点暂停，等待应用或人工参与者？」。**核心主线固定（用户 2026-08-05 指定，写作不得偏离）**：Interrupt 让 Graph Runtime 在可恢复执行点暂停，并把控制权交还应用或人工参与者；恢复时通过同一 thread 的持久化状态继续执行，并可携带人工输入或控制结果。Interrupt 不是 END，不是普通异常，也不等于完整的 HITL 业务流程；Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复协议。

## 需要新增

- `docs/03-langgraph-core/ch15-interrupt.md`（15.1-15.10 结构，回答 Q1-Q10，5 张 Mermaid 图）
- `.ai/tasks/TASK-0022-chapter-15-interrupt.md`（本文件）

## 需要修改

- `mkdocs.yml`（LangGraph Core 导航加入第 15 章）
- `docs/03-langgraph-core/index.md`（第 15 章条目改为链接 + 描述）
- `docs/00-introduction/content-map.md`（新增第 15 章行，状态「实现完成 / 待架构审查」；Part 3 行更新）
- `ROADMAP.md`（v0.4.0 新增 Chapter 15 条目，draft / 待架构审查）
- `.ai/context/current.md`

## 约束

- **核心主线固定**（见目标），不得偏离
- **Runtime 第一视角、Framework 第二视角**：先引用 Part 02 / Part 03 已建立语义（ch01 Human Stop 暂停态 / ch09 END / ch10 异常边界 / ch13 Command 作用域 / ch14 Checkpoint 承载），再讲 Interrupt 协议；禁止从 API 出发解释概念
- **三条硬边界**：Interrupt ≠ END（暂停 vs 终止）；≠ 普通异常（预期控制点 vs 失败路径）；≠ 完整 HITL 业务流程（原语 vs 审批流程 / 超时 / 审计 / 权限——Part 05）
- **Checkpoint 承载 + Interrupt 协议**：暂停跨进程存活依赖持久化承载（ch14）；恢复 = 第 14 章续跑场景（同一 thread 持久化状态继续）；两个原语不是一回事
- **恢复携带输入或控制结果**：人工输入（批准 / 拒绝 / 修改，T07 语义）+ 控制结果（Command——第 13 章作用域声明，API 不展开）；合并新输入的语义属应用契约 / Part 05
- **T07 挂载点**：人工审批 = Human Stop 暂停态挂载点（architecture-map）；审批规则本身属策略层 / 业务规则（ADR-004 / ADR-005）
- **不提前展开**：Interrupt API 写法与调用细节（框架 API 教程）、生产 HITL 完整语义（Part 05）、审批 UI / 通道（超出范围）、Stream（ch16，与暂停正交）、Subgraph（ch17）
- **当前 Demo 未使用**：如实标注（第 1 章声明未实现 / references 核验记录 / README 第 18 节 / examples/checkpoint_hitl 预留 / architecture-map 挂载点）
- **证据诚实**：仓库无 Interrupt 实现证据——基于第 1 章暂停态定义、官方核验记录与预留声明；未验证清单 5 项如实标注；不推断实现行为
- 测试数量以最新 CI 为准不写死
- 不修改 TASK-0014、Chapter 08-14、examples、tests、principles、ADR、依赖、Part 03 冻结顺序、Future LangChain Scope、Part 编号

## 验收标准

- [ ] 章节结构 15.1-15.10 完成，Q1-Q10 全部回答
- [ ] 固定主线逐字保持
- [ ] 5 张 Mermaid 图（暂停-恢复生命周期 / Interrupt 与 END-异常三态对比 / Checkpoint 承载 + Interrupt 协议 / 恢复注入人工输入或控制结果 / 当前 Demo 未使用教学边界）
- [ ] `mkdocs build --strict`、`git diff --check`、`pytest`、`ruff check .` 通过（测试数量以最新 CI 为准）
- [ ] content-map / ROADMAP / index / mkdocs 四源更新
- [ ] TASK-0022 Status = in_progress；ROADMAP Chapter 15 = draft / 待架构审查；content-map 第 15 章 = 实现完成 / 待架构审查；Part 03 保持进行中
- [ ] PR 创建（分支 feature/chapter-15-interrupt，commit `docs: draft chapter 15 interrupt`）
- [ ] 等待 Architecture Review

## 完成记录

- 2026-08-05：任务创建，正文初稿完成（待补）
