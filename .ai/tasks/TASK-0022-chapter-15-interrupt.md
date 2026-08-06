# TASK-0022：Chapter 15《Interrupt——暂停与人工介入》

## 元信息

| 字段 | 值 |
|---|---|
| Status | completed |
| Owner | AnRun-M |
| Created | 2026-08-05 |
| Updated | 2026-08-05 |
| Related ADR | ADR-0001 / ADR-0003 / ADR-0004 / ADR-0005 |
| Related Chapter | 第 1 章（Human Stop 暂停态）、第 9 章（END 哨兵）、第 10 章（异常 / 错误边界）、第 13 章（Command 作用域）、第 14 章（Checkpoint 承载）；TASK-0014（Part 03 规划，ch15 定位） |
| Related Example | examples/basic_langgraph（README 第 18 节：HITL 属 v0.4.0 / v0.6.0 里程碑）、examples/checkpoint_hitl（预留） |
| Related Test | 无（Demo 未使用，如实标注；证据为第 1 章声明 / 官方核验记录） |

## 目标

编写 Part 03 第七个原语章 `docs/03-langgraph-core/ch15-interrupt.md`：回答「图执行如何在可恢复执行点暂停，等待应用或人工参与者？」。**核心主线固定（用户 2026-08-05 指定，2026-08-06 Review 与合并前清理统一为最终表述，写作不得偏离）**：Interrupt 让 Graph Runtime 在可恢复执行点暂停，并把控制权交还应用或人工参与者；恢复时使用同一 thread 的持久化状态，包含 Interrupt 的 Node 会从头重新执行，直到 `interrupt()` 取得 resume payload 后继续后续逻辑——恢复调用通过 Runtime 控制封装携带 resume payload，payload 可以是人工审批结果、修改内容、澄清信息或其他结构化输入；Interrupt 在业务语义上不是失败，但在 LangGraph 实现中通过特殊控制流异常通知 Graph Runtime 暂停；Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复值注入协议。

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
- **业务语义与实现机制两层**：业务语义上 Interrupt 不是失败（≠ FAILED State、不进普通业务错误路径）；LangGraph 实现中 interrupt() 经**特殊控制流异常**通知 Graph Runtime 暂停（Runtime 捕获信号、保存 checkpoint、暴露 payload）——**普通 try/except 不应吞掉暂停信号**、不能当普通业务异常处理
- **Resume 时 Node 重执行语义**："从暂停点恢复"是**图执行语义，不是 Python 指令级 continuation**——包含 Interrupt 的 Node 从头重新执行，直至 interrupt() 取得 resume value 后继续后续逻辑；**工程影响**：Interrupt 前副作用必须幂等、不可安全重复的外部写入不得放在 Interrupt 前、多个 Interrupt 顺序必须稳定（生产幂等治理 Part 05）
- **Resume payload 与 Command 区分**：① Resume payload（approved / edited_sql / approval_feedback / clarification / 结构化审批决定，应用或人工产生）② Command(resume=payload) 恢复同一 thread（Runtime 控制封装）③ payload 成为 interrupt() 返回值；**Interrupt Payload Contract**：可序列化 / 大小受控 / 不携带连接对象或运行时句柄 / 敏感字段受权限与脱敏约束 / 大对象用 ID-URI-digest-summary 引用
- **生命周期状态归属**：RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING 是第 1 章建立的**应用生命周期语义**，不是 LangGraph 自动写入的 Graph State 字段——LangGraph 提供暂停协议，业务状态字段由应用契约维护（Graph State / Task Store / 审批系统）
- **五层职责（修正"恢复后去哪"归属）**：Application Node-Policy（何处触发 / 定义 payload / resume 后业务处理）→ Interrupt protocol（暂停 / 暴露 payload / 提供 resume value）→ Checkpointer（保存读取 thread 状态）→ Node-Command-Edge（根据 resume value 产生 Update / 表达路由意图）→ Graph Runtime（恢复执行 / 解释 / 调度）
- **Checkpointer 持久性限定**：可恢复 Interrupt 需要 Checkpointer 与稳定 thread_id；跨进程 / 重启 / 迁移恢复还需 **durable persistence backend**（内存型 saver 只适合教学或单进程，不等于生产持久化）
- **三条硬边界**：Interrupt ≠ END（暂停 vs 终止）；≠ 普通异常（业务语义 + 实现机制两层）；≠ 完整 HITL 业务流程（原语 vs 审批流程 / 超时 / 审计 / 权限——Part 05）
- **Checkpoint 承载 + Interrupt 协议**：暂停跨进程存活依赖持久化承载（ch14）；恢复 = 第 14 章续跑场景（同一 thread 持久化状态继续）；两个原语不是一回事
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
- [x] PR #41 Architecture Review 七项修正全部应用（业务语义 / 特殊异常实现桥接 / Resume 时 Node 重执行 / Resume payload 与 Command 区分 / WAITING_FOR_HUMAN 生命周期归属 / 五层职责 / Payload Contract / durable backend 边界）
- [x] PR #41 合并前一致性清理全部应用（15.1 旧恢复语义清理 / PR 顶部摘要直接同步最终结论 / Resume payload 与 Command 固定主线统一）
- [x] PR #41 复审通过并 squash merge 到 main（commit b9ef9fe，CI build/test 双绿，2026-08-06）→ Chapter 15 最终完成
- [x] `.ai/context/current.md` 已更新

## 完成记录

- 2026-08-05：任务创建，正文初稿完成；四源更新；PR #41 创建。
- 2026-08-06：**PR #41 Architecture Review 七项修正**（commit：docs: refine interrupt resume and lifecycle boundaries）全部应用并推送更新 PR #41：
  1. **业务语义与实现机制两层**（15.2 / 15.5 / 三态表 / Q4 / 误区 #2）：业务语义非失败（≠ FAILED State）；实现上 interrupt() 经特殊控制流异常通知 Runtime 暂停（捕获信号 / 保存 checkpoint / 暴露 payload）——普通 try/except 不应吞掉信号
  2. **Resume 时 Node 重执行语义**（主线 / 15.1 / 15.2 Mermaid / 15.3 / 15.4 / 15.5 / Q2 / Q5 / Q6 / 误区 #5）："从暂停点恢复"是图执行语义非指令级 continuation——Node 从头重新执行直至 interrupt() 取得 resume value；工程影响（副作用幂等 / 不可安全重复写入 / Interrupt 顺序稳定）
  3. **Resume payload 与 Command 区分**（15.4 / Mermaid / Q6）：三层——resume payload（应用或人工产生）→ Command(resume=payload) 恢复同一 thread → payload 成为 interrupt() 返回值；payload 与 Command wrapper 概念分离
  4. **WAITING_FOR_HUMAN 生命周期归属**（15.1 / 15.5 表 / 生命周期 Mermaid / 15.7 / Q7）：应用生命周期语义非 LangGraph 自动写入的 State 字段；业务状态字段由应用契约维护（Graph State / Task Store / 审批系统）
  5. **五层职责**（15.3 / 15.4 / 15.6 / Q5 / Q6）：Application Node-Policy / Interrupt protocol / Checkpointer / Node-Command-Edge / Graph Runtime；删除"Interrupt 负责恢复后去哪"
  6. **Interrupt Payload Contract**（15.4）：可序列化 / 大小受控 / 不含连接对象与运行时句柄 / 敏感字段受权限脱敏约束 / 大对象用引用
  7. **Checkpointer 持久性限定**（15.3 / 误区 #4）：Checkpointer + 稳定 thread_id；跨进程恢复还需 durable persistence backend（内存型 saver 不等于生产持久化）
- 2026-08-06：**PR #41 合并前一致性清理**（commit：docs: align interrupt resume summary and terminology）：删除 15.1 残留错误句（"从暂停点继续，而不是从头或从异常路径重来"→"从持久化的图执行位置继续，而不是重新启动整张图；但包含 interrupt() 的 Node 会从头重新执行"）；PR #41 描述顶部摘要直接同步最终结论（章节定位固定主线 / Q2-Q7 摘要 / 关键边界 / Mermaid 行，非仅追加修正节）；固定主线中"可携带人工输入或控制结果"收窄为"恢复调用通过 Runtime 控制封装携带 resume payload；payload 可以是人工审批结果、修改内容、澄清信息或其他结构化输入"——同步至正文顶部 / 15.2 / 15.4 / TASK-0022 / current.md 两处。
- 2026-08-06：PR #41 经 Architecture Review 复审通过，squash merge 到 main（commit b9ef9fe，CI build/test 双绿）→ **TASK-0022 标记 completed；Chapter 15 最终完成**；本 Memory PR（docs/post-pr41-merge-memory）收敛状态（ROADMAP / content-map / current.md）。
