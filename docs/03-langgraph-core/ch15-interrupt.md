# 第 15 章：Interrupt——暂停与人工介入

> 状态：draft（2026-08-05）
> 前置阅读：第 1 章（Agent Loop / Human Stop 暂停态）、第 13 章（Command）、第 14 章（Checkpoint）、`docs/04-text2sql/canonical-pipeline.md`（T07 人工审批）、`examples/basic_langgraph`（README 第 18 节）、`references/official/langgraph.md`
> 本章回答 "**图执行如何在可恢复执行点暂停，等待应用或人工参与者？**"——Interrupt 是 Part 03 的第七个原语：暂停与恢复协议。
> 本章**不**讲 Interrupt API 的写法与暂停 / 恢复的调用细节（属框架 API 教程，超出本书范围）；**不**讲生产 HITL 完整语义（审批流程、超时、审计、权限——Part 05）；**不**讲真实审批 UI / 通道（超出范围）；**不**讲 Stream（第 16 章，流与暂停正交）。Runtime → LangGraph 全映射表是 Part 03 的全局参考（对应行：Interrupt / Human Stop 暂停态 → `interrupt()`），本章引用该行，不复制整表。

**整章主线（固定）：**

> **Interrupt 让 Graph Runtime 在可恢复执行点暂停，并把控制权交还应用或人工参与者；恢复时通过同一 thread 的持久化状态继续执行，并可携带人工输入或控制结果。Interrupt 不是 END，不是普通异常，也不等于完整的 HITL 业务流程；Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复协议。**

## 15.1 为什么需要 Interrupt

第 1 章 1.5 定义了第四种终止方式之外的**暂停态（Human Stop）**：RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING——"停一下再走"，当时明确标注"当前 Demo 未实现，留待 Interrupt 章节"。canonical 流程把它挂载到 **T07 人工审批**（`docs/04-text2sql/canonical-pipeline.md`：高风险查询支持人工审批；architecture-map：T07 人工审批 = Human Stop 暂停态挂载点，未实现）。

**为什么需要 Interrupt（Q1 的回答）**：高风险管理需要"执行到关键点 → 停下来 → 等人确认 → 再继续"的控制流（例如 T07：SQL 通过静态校验但风险高，需要人工批准后才执行）：

- **模型不能自己暂停**：暂停是执行控制行为，不是语义决策（第 1 章 1.4：循环与调度属于 Runtime）
- **普通终止不够**：SUCCESS / FAILED / MAX_ITERATIONS_REACHED 都是"结束"，而暂停是"未结束，等待继续"（第 1 章 1.5 状态机）
- **普通异常不够**：异常是失败路径，暂停是**预期的、可恢复的**控制点（15.5）

**Interrupt 解决这个问题**：让 Graph Runtime 在**可恢复执行点**暂停，把控制权交还应用或人工参与者；恢复后**从暂停点继续**，而不是从头或从异常路径重来（15.3）。

## 15.2 Interrupt 的定义与边界

**固定主线第一部分**：

> **Interrupt 让 Graph Runtime 在可恢复执行点暂停，并把控制权交还应用或人工参与者。**

```mermaid
flowchart LR
    subgraph EXEC["图执行"]
        N1["节点执行"] --> P["可恢复执行点"]
        P -->|"Interrupt：暂停"| OUT["控制权交还应用 / 人工参与者"]
        OUT -->|"恢复（携带输入或控制结果）"| N2["从暂停点继续执行"]
    end
```

四个要点：

1. **在可恢复执行点暂停**：不是任意位置——暂停点是**可以持久化并恢复**的执行位置（15.3 的 Checkpoint 承载）
2. **把控制权交还应用或人工参与者**：暂停期间图不再推进；由外部决定"继续、修改后继续、还是放弃"（T07 审批语义）
3. **恢复时通过同一 thread 的持久化状态继续执行**（固定主线第二部分，15.3）
4. **恢复时可携带人工输入或控制结果**（固定主线第三部分，15.4）

**三条硬边界（固定主线第四部分）**：

- **Interrupt 不是 END**：END 是图执行结束（第 9 章 9.6 / 第 11 章 11.8）；Interrupt 是**暂停**——图没有结束，等待继续
- **Interrupt 不是普通异常**：异常是失败路径（FAILED + failure_reason，第 10 章 10.7）；Interrupt 是**预期的控制点**——不是错误
- **Interrupt 不等于完整的 HITL 业务流程**：Interrupt 是**暂停与恢复原语**；审批流程、超时、审计、权限是**业务流程**（Part 05 / 策略层，15.6）

## 15.3 Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复协议

**固定主线最后部分**：

> **Checkpoint 提供持久化承载，Interrupt 提供暂停与恢复协议。**

第 14 章已建立：Checkpoint 是执行时刻的状态与执行上下文快照，支持恢复 / 重放 / 续跑（第 14 章 14.4 的续跑场景）。Interrupt 的暂停 **依赖这个持久化承载**（TASK-0014 规划原话："Interrupt 依赖 Checkpointer 实现暂停与恢复"）：

```mermaid
flowchart LR
    subgraph PAUSE["暂停（Interrupt 协议）"]
        P1["Graph Runtime 在可恢复执行点暂停"]
        P2["同一 thread 的持久化状态（Checkpoint 承载，第 14 章）"]
    end
    subgraph RESUME["恢复（Interrupt 协议）"]
        R1["外部：应用或人工参与者"]
        R2["携带人工输入或控制结果"]
        R3["通过同一 thread 持久化状态继续执行"]
    end
    P1 --> P2
    R1 --> R2 --> R3
    P2 -. "恢复时读取" .-> R3
```

**为什么必须有 Checkpoint（Q5 的回答）**：

- **暂停跨进程存活**：暂停期间进程可能结束、重启、迁移——暂停点与执行状态必须**持久化**，否则"暂停"退化为"中止"
- **恢复是续跑**：恢复 = 第 14 章 14.4 的**续跑（Resume）**场景——通过同一 thread 的持久化状态继续执行，而不是从头开始
- **没有 Checkpoint 就没有可恢复的暂停**：这是 ch01 Human Stop 暂停态（第 1 章 1.5）"留待 Interrupt 章节"的原因——暂停语义在第 1 章已定义，**持久化承载在第 14 章才建立**（集成点 ≠ 能力自动生效，第 8 章 8.4）

**职责分工**：Checkpoint 负责"状态能恢复"（持久化机制，第 14 章 14.3）；Interrupt 负责"什么时候暂停、恢复后去哪"（暂停与恢复协议）——**承载与协议是两个原语，不是一回事**。

## 15.4 恢复时携带人工输入或控制结果

**固定主线第三部分**：

> **恢复时通过同一 thread 的持久化状态继续执行，并可携带人工输入或控制结果。**

Q6 的回答——恢复不只是"回到暂停点"：

- **人工输入**：审批者给出批准 / 拒绝 / 修改意见（T07 语义：人工审批反馈进入执行）
- **控制结果**：恢复时可以携带**控制结果**（例如 Command——第 13 章已声明"Interrupt resume 时注入 Command"属本章场景，但 Command 的 API 机制不展开，见第 13 章 13.2 作用域声明）

```mermaid
flowchart LR
    OUT["外部参与者"] --> IN["人工输入或控制结果\n（批准 / 拒绝 / 修改 / Command）"]
    IN --> RES["恢复：同一 thread 持久化状态 + 新输入"]
    RES --> CONT["从暂停点继续执行"]
```

**边界**：恢复时"合并新输入的语义"（如何与已持久化状态结合、拒绝后走什么路径）属于**应用契约与 Part 05 生产语义**（第 14 章 14.3 同款边界）；本章只立"可携带人工输入或控制结果"这一语义。

## 15.5 Interrupt 与 END、异常的区别

Q3 / Q4 的回答——三种控制流形态的对比（第 1 章 1.5 状态机 + 第 9 章 END + 第 10 章错误边界的合流）：

| 形态 | 语义 | 图执行状态 | 是否可恢复 |
|---|---|---|---|
| **END（终止）** | 图执行结束（第 9 章 9.6） | 最终 State 返回调用方 | 否（除非重放，第 14 章） |
| **异常（失败）** | 失败路径：FAILED + failure_reason（第 10 章 10.7） | 失败 State | 否（生产恢复属 Part 05） |
| **Interrupt（暂停）** | 预期的、可恢复的控制点（本章） | **暂停态：RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING**（第 1 章 1.5） | **是——从暂停点继续** |

**一句话**：END 是"走完了"、异常是"走坏了"、Interrupt 是"停一下再走"（第 9 章 9.6 的表述延续）——三者不可互换：不能把人工审批画成 END（第 11 章 11.8：Human Stop 是暂停，不能简单画成 END），也不能把暂停当异常处理（暂停不是失败）。

## 15.6 与完整 HITL 业务流程的边界

Q8 的回答——**Interrupt 不等于完整的 HITL 业务流程**（固定主线硬边界）：

| Interrupt 原语（本章） | 完整 HITL 业务流程（Part 05） |
|---|---|
| 在可恢复执行点暂停（协议） | 审批流程定义（谁审批、几级、什么条件触发） |
| 恢复时携带人工输入或控制结果 | 审批超时与过期处理 |
| 提供暂停与恢复的执行语义 | 审批审计与权限 |
| 由应用在需要处挂载 | 策略层如何裁决审批（ADR-004 确定性策略层） |

**T07 挂载点（Q9 的回答）**：canonical T07 的"人工审批"部分 = Human Stop 暂停态挂载点（architecture-map 原话）——本章的 Interrupt 语义就是该挂载点的图化承载；但**审批规则本身**（什么风险等级必须审批、谁有权批准）属于确定性策略层 / 业务规则（ADR-004 / ADR-005），**不在 Interrupt 原语内**。

## 15.7 当前 Demo 为什么未使用

Q7 的回答——**如实标注**（与第 14 章 Checkpoint 同款教学边界）：

| 事实 | 证据 |
|---|---|
| 第 1 章已定义 Human Stop 暂停态但标注"未实现，留待 Interrupt 章节" | `docs/01-agent-foundations/ch01-agent-loop.md` 1.5 |
| 官方核验记录：Interrupt（Human-in-the-loop）列入"刻意未使用" | `references/official/langgraph.md` |
| HITL 属 v0.4.0 / v0.6.0 里程碑，届时基于本 Demo 扩展 | `examples/basic_langgraph/README.md` 第 18 节 |
| 预留示例目录 | `examples/checkpoint_hitl/`（README 预留） |
| architecture-map：T07 人工审批 = Human Stop 暂停态挂载点（未实现） | `.ai/principles/architecture-map.md` 第五/六节 |

**教学意义**：当前 Demo 的"无暂停"（顺序执行到 END）与"无 Checkpoint"（第 14 章）是配套的教学边界——**先理解暂停的语义需求（第 1 章）、再理解持久化承载（第 14 章）、最后才是暂停与恢复协议（本章）**；三者都是"集成点先存在、能力后接入"（第 8 章 8.4）。生产 HITL 属 v0.6.0 里程碑（Part 05）。

## 15.8 证据与测试

**必须诚实标注：当前仓库没有 Interrupt 的实现与执行证据**（Q10 的回答）：

| 证据类型 | 内容 |
|---|---|
| 概念坐标 | 第 1 章 1.5：Human Stop 暂停态（RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING，未实现） |
| 核验记录 | `references/official/langgraph.md`：Interrupt（Human-in-the-loop）列入"刻意未使用" |
| 预留 | `examples/checkpoint_hitl/` 目录存在（README 预留）；README 第 18 节：HITL 属 v0.4.0 / v0.6.0 里程碑 |
| canonical 挂载点 | T07 人工审批 = Human Stop 暂停态挂载点（architecture-map） |

**未验证清单**（仓库中无证据，如实标注）：

- Interrupt 的暂停 / 恢复行为（API 语义）
- 恢复时注入人工输入 / 控制结果的机制
- 同一 thread 恢复与 Checkpoint 的组合行为（第 14 章 14.4 续跑场景的 Interrupt 形态）
- 暂停期间的并发 / 幂等行为
- 生产 HITL 完整语义（审批流程、超时、审计、权限——Part 05）

（测试数量以最新 CI 为准，不在正文写死；本章结论基于第 1 章暂停态定义、官方核验记录与预留声明，不推断实现行为。）

## 15.9 常见误区

1. **Interrupt 就是 END**——END 是图执行结束（第 9 章 9.6）；Interrupt 是暂停，图未结束，等待继续（15.2）
2. **Interrupt 就是异常**——异常是失败路径（第 10 章 10.7）；Interrupt 是预期的、可恢复的控制点（15.5）
3. **Interrupt 等于完整 HITL**——Interrupt 是暂停与恢复原语；审批流程、超时、审计、权限属 Part 05（15.6）
4. **没有 Checkpoint 也能暂停**——暂停跨进程存活依赖持久化承载；Checkpoint 提供承载、Interrupt 提供协议（15.3）
5. **恢复就是从头重跑**——恢复是续跑：通过同一 thread 的持久化状态从暂停点继续（15.3 / 第 14 章 14.4）
6. **暂停期间模型自己会继续**——控制权已交还应用或人工参与者，图不再推进（15.2）
7. **审批规则是 Interrupt 的一部分**——审批规则（什么必须审、谁有权批）属确定性策略层 / 业务规则（ADR-004 / ADR-005）；Interrupt 只提供暂停与恢复（15.6）
8. **当前 Demo 已经支持暂停**——第 1 章已定义暂停态但未实现；references 核验记录刻意未使用；examples/checkpoint_hitl 预留（15.7）
9. **Interrupt 能自己持久化**——持久化是 Checkpoint 的职责（第 14 章）；Interrupt 是协议（15.3）
10. **暂停与流式是同一能力**——Stream（第 16 章）是"边跑边看"，Interrupt 是"停一下再走"——两者正交（本章边界）

## 15.10 总结

| # | 问题 | 答案 |
|---|---|---|
| Q1 | 为什么需要 Interrupt？ | 高风险管理需要"执行到关键点 → 停下来 → 等人确认 → 再继续"的控制流（T07 人工审批挂载点）；模型不能自己暂停、普通终止与异常都不是"预期的可恢复暂停" |
| Q2 | Interrupt 是什么？ | 让 Graph Runtime 在可恢复执行点暂停，把控制权交还应用或人工参与者；恢复时通过同一 thread 的持久化状态继续执行 |
| Q3 | Interrupt 与 END 有什么区别？ | END 是图执行结束（最终 State 返回）；Interrupt 是暂停——图未结束，等待继续（不能把审批画成 END） |
| Q4 | Interrupt 与普通异常有什么区别？ | 异常是失败路径（FAILED + failure_reason）；Interrupt 是预期的、可恢复的控制点 |
| Q5 | 为什么必须有 Checkpoint？ | 暂停跨进程存活需要持久化承载；恢复 = 第 14 章续跑场景（同一 thread 状态继续）；Checkpoint 提供承载、Interrupt 提供协议 |
| Q6 | 恢复时如何注入人工输入或控制结果？ | 恢复可携带人工输入（批准 / 拒绝 / 修改）或控制结果（Command——第 13 章作用域声明，API 不展开）；合并新输入的语义属应用契约 / Part 05 |
| Q7 | 与 ch01 Human Stop 暂停态如何对应？ | 状态机同源：RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING（第 1 章 1.5）；本章提供该暂停态的图化协议 |
| Q8 | Interrupt 等于完整的 HITL 业务流程吗？ | 不等于——原语 vs 业务流程（审批流程 / 超时 / 审计 / 权限属 Part 05） |
| Q9 | 与 T07 人工审批的关系？ | T07 人工审批 = Human Stop 暂停态挂载点（architecture-map）；Interrupt 是挂载点的图化承载；审批规则本身属策略层 / 业务规则 |
| Q10 | 已验证什么、未验证什么？ | 已验证：第 1 章暂停态定义 / 官方核验记录（刻意未使用）/ 预留声明；未验证：暂停恢复行为、输入注入机制、Checkpoint 组合、并发幂等、生产 HITL 语义 |

**本章验收标准：**

- [ ] 能复述固定主线：Interrupt 在可恢复执行点暂停并把控制权交还应用或人工参与者；恢复时通过同一 thread 持久化状态继续并携带人工输入或控制结果；不是 END、不是普通异常、不等于完整 HITL；Checkpoint 提供承载、Interrupt 提供协议
- [ ] 能区分 END（终止）/ 异常（失败）/ Interrupt（暂停）三种控制流形态
- [ ] 能说明 Interrupt 与 Checkpoint 的分工（承载 vs 协议）与"为什么必须有 Checkpoint"
- [ ] 能说明恢复时携带人工输入或控制结果的语义（合并规则属应用契约 / Part 05）
- [ ] 能对应 ch01 Human Stop 暂停态（RUNNING → INTERRUPTED / WAITING_FOR_HUMAN → RUNNING）
- [ ] 能说明 Interrupt ≠ 完整 HITL（审批流程 / 超时 / 审计 / 权限属 Part 05）与 T07 挂载点关系
- [ ] 能如实标注当前 Demo 未使用的教学边界（第 1 章声明 / 核验记录 / 预留示例）
- [ ] 能诚实标注证据范围（无实现证据；不推断实现行为）
- [ ] 术语与 `TERMINOLOGY.md` 一致；只引用不重新定义 Human Stop 暂停态 / Checkpoint / Command 语义

**本章边界**：Human Stop 暂停态语义——第 1 章 1.5；Checkpoint（持久化承载）——第 14 章；Command（恢复时注入控制结果）——第 13 章作用域声明；Stream（与暂停正交）——第 16 章；Subgraph——第 17 章；生产 HITL 完整语义（审批流程 / 超时 / 审计 / 权限）——Part 05；审批 UI / 通道——超出范围；LangChain——Future LangChain Scope Planning（`.ai/context/current.md` Future Task），不在本章展开。
