# 第 7 章：Memory、Context 与 Context Management

> 状态：draft（2026-08-01）
> 前置阅读：第 2 章（Execution State）、第 3 章（Model Context）、第 4 章（Prompt Builder）、第 6 章（Runtime Scheduler）、`.ai/principles/architecture-map.md`（第三 / 四 / 五层）、`.ai/principles/state-design.md`
> 本章是 **Part 02 的最后一个规划章节**（Part 02 收官前置）：讲清 Memory / State / Model Context / Checkpoint 的边界，以及 Context Management 的基础 Runtime 语义。
> 不讲：向量数据库选型、Embedding、RAG 检索算法、BM25、向量相似度、Knowledge Graph、MCP、LangGraph Memory / Checkpointer API、具体数据库实现、长期记忆产品方案。

**整章主线：**

> **State 服务于一次 Agent 执行；Model Context 服务于一次模型调用；Memory 跨越执行边界；Checkpoint 保存执行状态快照。Context Management 负责在预算、权限和事实边界内，为本次模型调用选择、裁剪、压缩并注入所需信息。**

## 7.1 为什么需要 Context Management

从前几章的执行链出发（State → Prompt Builder → Model Context → Model，第 6 章 6.6），真实系统中模型调用的**输入来源不断增多**：

- User Message
- State Slice
- Tool Result
- Recent History
- System Instruction
- Policy Metadata
- Retrieved Facts
- Memory Candidates

**问题不是"有没有数据"，而是：本次调用真正应该让模型看到什么？**

- 全部来源都塞进 Context → 超出预算、引入噪声、冲突事实、权限泄漏（第 3 章 3.3 的最小充分上下文原则）
- 只塞 State → 丢失历史、偏好、环境信息

**Context Management 不是简单拼接**——它是受**预算、权限、相关性、事实时效和生命周期**约束的**输入治理**（第 4 章 4.2 的输入选择在此系统化）。它与第 5 章 Tool View（请求级可用性过滤）是同一类问题：**暴露什么给模型，由治理决定，不由"数据存在"决定**。

诚实标注：`examples/manual_agent_loop` 与 `examples/basic_langgraph` **没有独立 Context Manager**——`FakeLLM` 直接读 State（`StateProxy`）。本章描述的 Pipeline 是 **Runtime 的逻辑抽象**，不是已实现状态。

## 7.2 四个概念的边界

| 维度 | Execution State | Model Context | Memory | Checkpoint |
|---|---|---|---|---|
| **生命周期** | 一次执行 | 一次模型调用 | 跨执行（跨任务 / 跨会话） | 快照时刻 |
| **服务对象** | Runtime（Observe / Update） | 模型（一次调用） | 未来执行 / 任务 / 会话 | 恢复 / 重放 / 续跑 |
| **是否跨执行** | 否（同一次执行内跨轮） | 否 | **是（区分轴）** | 否（是 State 的快照） |
| **是否是事实源** | 是（执行控制事实） | 否（组装产物） | 是（跨执行信息） | 否（State 的持久化副本） |
| **写入者** | Runtime（apply_* / 节点更新） | Runtime（Builder） | Memory 写入流程（7.8） | Runtime / Checkpointer |
| **读取者** | Runtime、Policy、经切片给模型 | 模型 | Runtime（检索后注入 Context） | Runtime |
| **主要用途** | 下一轮决策的控制事实 | 本次调用的可见输入 | 跨执行复用信息 | 崩溃恢复、重放、审计快照 |
| **不是什么** | 不是 Context / Memory / Checkpoint | 不是 State / Memory | 不是 State / Context / Checkpoint | 不是 Memory（即使保存得久） |

六个必须成立的边界：

- **State ≠ Context**（服务对象不同：执行 vs 调用）
- **State ≠ Memory**（区分轴：是否跨越单次执行边界）
- **State ≠ Checkpoint**（Checkpoint 是 State 的快照，不是 State 本身）
- **Context ≠ Memory**（Context 是一次调用快照；Memory 是跨执行信息）
- **Memory ≠ Checkpoint**（Memory 是跨执行信息；Checkpoint 是执行快照）
- **Checkpoint 可能被长期保存，但"保存得久"不等于 Memory**——快照是 State 的副本，不是为未来执行选择的信息

```mermaid
flowchart TD
    EXEC["一次 Agent 执行"]
    ST["Execution State（执行控制事实源）"] --> CTX["Model Context（一次调用快照）"]
    CK["Checkpoint（State 的持久化快照）"] -. "恢复 / 重放 / 续跑" .-> EXEC
    MEM["Memory（跨越执行边界）"] -. "检索后注入" .-> CTX
    EXEC -. "边界" .-> EXEC2["下一次执行 / 新任务 / 新会话"]
    MEM --> EXEC2
```

## 7.3 为什么"跨轮次"不是 Memory

同一次 Agent 执行内部可能有 20 轮。**第 1 轮产生的信息在第 10 轮继续使用——它仍然可以只是 Execution State 或 History，不自动成为 Memory。**

判断标准只有一个：**是否将在新的执行、任务或会话中再次使用**（`.ai/principles/architecture-map.md` 第四节：区分轴 = 是否跨越单次执行边界）。

```mermaid
flowchart LR
    R1["第 1 轮"] --> R2["第 2 轮"] --> R3["..."] --> R10["第 10 轮"]
    R1 -. "validation_error 在第 2 轮继续使用" .-> R2
    R1 -. "仍在同一次执行内 → State / History" .-> R10
    R1 -. "跨到新会话（默认时区偏好）" .-> M["Memory 候选"]
```

Text-to-SQL 示例：

- 同一次修复 Loop 中，`validation_error` 在下一轮使用 → **State**，不是 Memory（第 2 章 2.4：字段在 State 里，因为它是本次执行的控制事实）
- 新用户会话继续记住"默认时区为 Asia/Shanghai" → **Memory 候选**（将跨执行使用）

## 7.4 History 与 Memory

| 概念 | 定义 | 关系 |
|---|---|---|
| **History** | 发生过什么的顺序记录或事件摘要（本项目的 `history` 字段，第 2 章 2.4） | Memory 的**候选来源** |
| **Memory** | 经过选择后，为未来执行保留的信息 | 不是 History 本身 |

**全量消息历史不等于长期记忆；日志不等于 Memory；Trace 不等于 Memory；`history` 字段也不天然等于 Memory**——History 是"发生过什么"的记录，Memory 是"经过选择、为未来保留"的信息（7.8 的写入流程决定什么成为 Memory）。

Text-to-SQL 示例：

- 最近两次 SQL 校验失败摘要 → 本次执行的 History / Context 候选（仍在一次执行内）
- 用户长期偏好的币种、时区 → Memory 候选（跨执行）
- 完整 SQL 结果集 → 外部事实引用（第 2 章 2.6 / 第 5 章 5.8 的引用策略），不应直接成为 Memory

## 7.5 Context Window 与预算

**Context Window 是模型容量约束；Context Budget 是 Runtime 为本次调用分配的可用预算**——两个概念必须分开：

- **Window**：模型一次能接受的最大输入容量（绑定具体模型，本章不绑定 token 数）
- **Budget**：Runtime 按策略为本次调用分配的份额（结合成本、优先级、租户配置）

**Context Management 不只是"防止超 token"**。预算之内还要考虑：

- **relevance**（相关性）、**authority**（来源权威性）、**freshness**（时效）
- **privacy**（隐私）、**tenant isolation**（租户隔离）、**provenance**（可溯源）
- **duplication**（去重）、**conflicting facts**（冲突事实处理）
- **cost**（成本）、**latency**（延迟）

Budget 由谁决定？Policy / Runtime Configuration（第 4 章 4.2 的"Policy 决定、Builder 执行"同一分工）——Context Manager 执行预算，不制定预算。

## 7.6 Context Management Pipeline

逻辑阶段（**不要求每次全部执行，不绑定具体类或实现**）：

```mermaid
flowchart LR
    C["Collect（收集候选）"] --> N["Normalize（规范化）"]
    N --> A["Authorize / Filter（授权与过滤）"]
    A --> R["Rank / Select（排序与选择）"]
    R --> T["Trim（裁剪）"]
    T --> CS["Compress / Summarize（压缩 / 摘要）"]
    CS --> I["Inject（注入）"]
    I --> M["Record Metadata（记录元数据）"]
```

各操作分别解决什么问题（Q7 的回答）：

| 操作 | 解决什么 | 特性 |
|---|---|---|
| **Selection** | 选择本次决策需要的信息 | 不改变内容 |
| **Trimming** | 删除低价值或超预算内容 | 通常不改变剩余内容语义 |
| **Compression** | 用更紧凑表示保留关键信息 | 保留语义 |
| **Summarization** | 产生新的摘要表达 | **存在信息丢失和模型偏差风险**——必须可追踪（7.9） |

**Injection 的边界**（Q9 部分 / 与第 4 章的衔接）：

- **Prompt Builder**：负责**结构化组装与渲染**（第 4 章 4.3：产出可发送的输入结构）
- **Context Manager**：负责**信息选择、预算与压缩治理**

两者可以在简单实现中合并，但**概念职责要分开**——组装是渲染问题，选择是治理问题。

## 7.7 Context Injection 与来源

```mermaid
flowchart LR
    subgraph SRC["输入来源"]
        S1["State Slice"]
        S2["Recent History"]
        S3["Tool Result Summary"]
        S4["Policy-derived Metadata"]
        S5["Retrieved Context"]
        S6["Memory Candidates / Records"]
        S7["User / Tenant Configuration"]
    end
    SRC --> G["进入本次 Context 前的治理检查"]
    G --> I["Inject → Prompt Builder / request payload"]
    G -->|"Authorization"| G
    G -->|"Tenant Isolation"| G
    G -->|"Provenance"| G
    G -->|"Freshness"| G
    G -->|"Size Control"| G
    G -->|"Conflict Handling"| G
```

来源可以很多，但进入本次 Context 前必须经过：**Authorization、Tenant Isolation、Provenance、Freshness、Size Control、Conflict Handling**（Q8 的回答）。

两个硬边界：

- **Context Manager 不创造业务事实**——它选择和转换已有输入
- **模型生成的摘要不能自动升级为权威业务事实**——摘要必须保留来源引用（7.9 的审计要求）

## 7.8 Memory 写入与读取边界

只讲基础语义，不讲存储实现。**Memory 写入不应是"每轮对话全部保存"。**

逻辑写入流程：

```mermaid
flowchart LR
    CAND["Candidate（候选）"] --> V["Validate（校验）"]
    V --> CL["Classify（分类）"]
    CL --> AU["Authorize（授权）"]
    AU --> P["Persist（持久化）"]
    P --> VE["Version / Expire（版本与过期）"]
```

Memory 候选至少区分：

- **User Preference**（用户偏好）
- **Stable Business Configuration**（稳定业务配置）
- **Reusable Task Fact**（可复用任务事实）
- **Learned Strategy / Feedback**（学到的策略 / 反馈）
- **Sensitive Information**（敏感信息——需要额外策略）

明确（Q9 部分）：

- **并非所有内容都应该进入 Memory**——写入经过 Validate / Classify / Authorize
- **敏感信息需要额外策略**（脱敏、禁止写入或最小化）
- **Memory 必须有作用域**：user / tenant / application / task type
- **Memory 必须有生命周期**：TTL / invalidation / deletion / update
- **Memory 需要 provenance 和版本**
- **旧 Memory 可能过期或冲突**——读取时必须处理（7.7 的 Conflict Handling）

不规定向量数据库。

## 7.9 测试、版本与审计

五类测试必须区分（Q9 的回答）：

| 测试类型 | 断言什么 |
|---|---|
| **Context Manager Unit Test** | 给定相同输入、预算、策略和版本 → 生成可断言的选择结果与 payload metadata |
| **Compression / Summarization Test** | 关键事实保留、禁止信息泄漏、引用可追踪 |
| **Memory Read Test** | 作用域、权限、时效和冲突处理正确 |
| **Memory Write Test** | 只有允许的候选写入；敏感内容被拒绝或脱敏 |
| **Regression Test** | 代表性任务中，Context 策略变化不能导致不可接受的行为退化 |

审计元数据至少包括：**context policy version、prompt/template version、memory record ids / versions、retrieved source ids / versions、selection reason、trimming/compression strategy、token or size budget、payload digest、tenant/user/request metadata**（不展开 Observability 存储实现）。

## 7.10 常见误区

1. **"跨轮次数据就是 Memory"**：同一次执行内的跨轮使用仍是 State / History（7.3）。
2. **"全量聊天记录就是 Memory"**：History 是候选来源，不是 Memory 本身（7.4）。
3. **"Memory 就是向量数据库"**：Memory 是概念边界；存储与检索是实现（本章不选型）。
4. **"Context 越长越好"**：预算、相关性、冲突与权限约束（7.5）。
5. **"Summarization 没有信息损失"**：有信息丢失与模型偏差风险（7.6）。
6. **"Checkpoint 就是 Memory"**：Checkpoint 是 State 快照；"保存得久"不等于 Memory（7.2）。
7. **"Trace / Log 就是 Memory"**：可观测数据不是为未来执行选择的信息（7.4）。
8. **"Context Manager 可以创造事实"**：它选择和转换已有输入；模型摘要不能自动成为权威事实（7.7）。
9. **"所有 Tool Result 都应进入 Context"**：进入前必须经过治理检查（7.7）。
10. **"Memory 一旦写入就永久正确"**：有版本、过期、失效与冲突处理（7.8）。

## 7.11 总结

十个问题的浓缩答案：

| # | 问题 | 答案 |
|---|---|---|
| Q1 | State / Context / Memory / Checkpoint 分别是什么？ | State=一次执行的控制事实源；Context=一次调用可见快照；Memory=跨执行信息；Checkpoint=State 的持久化快照（7.2 表） |
| Q2 | 为什么"跨轮次"不能作为 Memory 定义？ | 同一次执行内跨轮使用仍是 State / History；判据是"是否将在新执行 / 任务 / 会话中再次使用"（7.3） |
| Q3 | 为什么 Memory 判据是"跨越一次执行边界"？ | 区分轴唯一且可判定：执行边界之内的信息可由 State 承载，之外的信息才需要 Memory（architecture-map 第四节） |
| Q4 | Context Management 是什么？为什么不等于 Memory？ | 为本次调用做选择 / 预算 / 裁剪 / 压缩 / 注入的输入治理；Memory 是信息来源之一，Management 是治理过程（7.1 / 7.6） |
| Q5 | History 与 Memory 有什么区别？ | History=顺序记录（候选来源）；Memory=经选择为未来保留的信息（7.4） |
| Q6 | 为什么不能全部塞入 Context？ | 预算、相关性、冲突、权限、租户隔离、成本与延迟约束（7.5） |
| Q7 | Selection / Trimming / Compression / Summarization 分别解决什么？ | 选择=挑所需；裁剪=删低价值；压缩=紧凑保语义；摘要=新表达（有信息丢失风险）（7.6） |
| Q8 | Context Injection 的来源与安全边界？ | 七类来源；进入前必须经 Authorization / Tenant Isolation / Provenance / Freshness / Size Control / Conflict Handling；Manager 不创造事实（7.7） |
| Q9 | Context Management 如何版本化、测试和审计？ | 五类测试 + 审计元数据集合（context policy version / memory record ids / selection reason / payload digest 等）（7.9） |
| Q10 | 与 RAG / Checkpoint / Observability / LangGraph 的边界？ | RAG 检索算法 → 后续章节；Checkpoint 机制 → Part 03 + 生产恢复 Part 05；Observability 存储 → Part 05；LangGraph Memory / Checkpointer API → Part 03——本章只讲基础语义 |

**本章不会讨论什么**（边界声明）：向量数据库选型、Embedding / Retrieval 算法、LangGraph Memory / Checkpointer API、生产级 Durable Recovery、Observability 后端、新增 Memory Demo、新增数据库依赖。

**本章验收标准：**

- [ ] 能画出四概念边界表并复述六个不等号（"保存得久 ≠ Memory"）
- [ ] 能用 Text-to-SQL 例子区分"跨轮次使用"（State）与"跨执行使用"（Memory 候选）
- [ ] 能区分 History 与 Memory 及三个反例（全量消息 / 日志 / Trace）
- [ ] 能区分 Context Window 与 Context Budget
- [ ] 能画出 Pipeline 并解释四操作的差异（Summarization 的信息丢失风险）
- [ ] 能说明 Prompt Builder（组装渲染）与 Context Manager（选择治理）的职责边界
- [ ] 能列出 Injection 的治理检查与"Manager 不创造事实"
- [ ] 能说明 Memory 写入流程、作用域与生命周期
- [ ] 能列出五类测试与审计元数据集合
- [ ] 能诚实标注 Demo 无跨执行 Memory / 无独立 Context Manager

**与 Demo 的关系（如实说明，不伪造实现）**：`examples/manual_agent_loop` 与 `examples/basic_langgraph` **有** Execution State、history、Tool Result、validation_error 等执行内信息；**没有**跨执行 Memory、独立 Context Manager、Compression / Summarization / Injection 组件；当前双 Runtime 等价测试**不验证** Memory 与 Context Management。这两个 Demo 可以作为：State / History 的**正例**、Memory 的**反例**、未来 Context Manager 的**输入来源示例**——不得写成 Chapter 07 能力已经实现。
