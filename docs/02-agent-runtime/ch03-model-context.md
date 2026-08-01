# 第 3 章：Model Context——Runtime 如何向模型构造世界

> 状态：draft（2026-08-01）
> 前置阅读：第 2 章（Execution State）、`.ai/principles/architecture-map.md`（第三层 Model Context）
> 本章回答：**模型看到的到底是什么？**——Runtime 如何把 State 与外部信息组装成一次模型调用。
> 不涉及 Prompt Engineering / Prompt Template / LangGraph API / Memory / Checkpoint / MCP / RAG（均属后续章节）。

**一句话主线：**

> **模型永远看不到整个 Runtime。它只能看到 Runtime 构造给它的那一次调用输入——这就是 Model Context。**

## 3.1 Runtime 为什么要构造 Context

第 2 章确立了：State 是 Runtime 侧的执行事实源。现在换到模型视角问一个问题：**模型看得到 State 吗？**

看 `examples/manual_agent_loop` 与 `examples/basic_langgraph` 的事实：

- 模型（`FakeLLM`）的输入接口是 `decide_next(state)` / `generate_sql(state)`——它接触到的不是"整个 Runtime"，而是**被传入的那份数据**
- 在 graph 版本中，这份数据甚至不是 `GraphState` 字典本身，而是 `StateProxy`（`nodes.py`）——一个**只读适配视图**，模型只能读、不能写、看不到字典外的任何东西
- 校验器、执行器、循环、终止判断——模型一律看不见

这是 Q1 的回答：

> **模型永远看不到整个 Runtime。** 它的世界边界就是 Runtime 构造并传入的那次调用输入。模型能知道什么，完全由 Runtime 决定。

推论：**"模型知道校验失败"这件事，不是模型的能力，而是 Runtime 的构造结果**（第 2 章 2.1 已述：校验结果写进 State，下一轮 Observe 读到；本章补充后半段：**Observe 之后还必须把 State 切片组装成模型可消费的形式**，模型才能"看到"）。

## 3.2 什么是 Model Context

`.ai/principles/architecture-map.md` 第三层的定义，本章以它为准：

> **Model Context：一次模型调用实际可见的输入。**

它是**组装产物**，不是存储。可能的来源：

| 来源 | 在本项目 Demo 中的形态 |
|---|---|
| **State 切片** | `decide_next` / `generate_sql` / `fix_sql` 收到的 `state`（manual）；`StateProxy(state)`（graph） |
| **Tool Result** | Validator 输出经 `apply_validation` 写入 State，下一轮进入模型输入（修复循环的机制，第 2 章 2.4） |
| **User Question** | `state["user_question"]`（ch02 字段表：目标是 Agent 的输入定义） |
| **System Instruction** | 本项目 Demo **未实现**显式 System Prompt 组装（FakeLLM 无指令概念）——这是与后续 Prompt Builder 章节的边界（3.9 / Q10） |

**Context 不是 State**（Q2）：State 是**一次执行**中持续存在的事实源；Context 是**一次调用**可见的组装快照。区分轴：State 服务于执行（跨轮），Context 服务于调用（不跨轮）——与 State/Memory 的区分轴（是否跨越单次执行边界，architecture-map 第四节）是同一个思路的不同层次。

## 3.3 State → Context

State 不会整体进入 Context。选择规则（Q3 的回答）：

**应该进入**：影响本次模型决策的字段——`user_question`、`current_sql`、`validation_error`、`validation_rule`、`execution_result`（摘要）。修复循环的机制就是证据：`FakeLLM.fix_sql` 读 `validation_rule` 决定怎么修（`models.py`）——这个字段**必须**在模型可见范围内。

**不应该进入**：纯控制字段——`iteration`、`max_iterations`、`status`、`history` 全文。模型决策不依赖它们（终止是确定性策略层的职责，第 1 章 1.5）；把控制字段塞进模型输入，等于让模型"假装拥有"它并不拥有的控制权。

```mermaid
flowchart LR
    subgraph STATE["Execution State（Runtime 侧）"]
        A1["user_question / current_sql / validation_error / validation_rule"]
        A2["execution_result（摘要）"]
        B1["iteration / status / max_iterations"]
        B2["history 全文"]
        B3["外部大对象（引用）"]
    end
    subgraph CTX["Model Context（模型侧，一次调用）"]
        C1["决策所需切片"]
        C2["Tool Result 摘要"]
        D["控制字段 ❌"]
        E["不相关事实 ❌"]
    end
    A1 --> C1
    A2 --> C2
    B1 -. "不进（终止由策略层保证）" .-> D
    B2 -. "不进（不是调用输入）" .-> D
    B3 -. "不进（只进引用）" .-> E
```

**最小切片原则**：Context 只放"影响本次决策"的信息。这与第 2 章 2.6 的引用策略同源——State 不复制外部事实，Context 也不复制 State 全文。

## 3.4 Context 生命周期

```mermaid
flowchart LR
    A["Loop 进入新的一轮"] --> B["Observe State"]
    B --> C["Build Model Context（组装：State 切片 + User Question + Tool Result 摘要 + System Instruction）"]
    C --> D["Model Decision（一次调用）"]
    D --> E["Context 失效：调用结束，组装产物丢弃"]
    E --> A
```

Q5 / Q6 的回答：

- **Context 是一次调用可见**：创建于调用前，失效于调用后。它不跨轮——下一轮重新组装，即使组装结果与上一轮相同，也是"新的 Context"
- **Context 可以变化而 State 不需要变化**：Context 是**组装产物**（每轮可重新组装，成本低）；State 是**事实源**（只在动作结果写回时更新）。第 1 轮和第 2 轮的 Context 不同（多了校验错误），是因为 State 更新了——**Context 的变化是 State 演化的投影，不是独立的变化源**

## 3.5 Prompt 与 Context

Q4 的回答：**Prompt 是 Context 的组成部分，不是 Context 本身。**

- Context = 组装产物（整体）：State 切片 + User Question + Tool Result 摘要 + System Instruction
- Prompt = System Instruction 组件（指令/约束部分）
- 类比：Context 是"给模型的一封信"，Prompt 是信里的"指令段落"——信还包括事实段落（State 切片、Tool 结果）

Q7 的回答（从 Context 视角重申第 2 章 2.8）：

- **Prompt 可以频繁修改**：它只是 Context 组装中的一个组件。修改 Prompt = 换一段指令，不影响 State Schema、不影响其他组件、不影响其他 Runtime——但它是**模型行为策略**（第 2 章 2.8：可能改变 next action / Tool 参数 / 路径 / 最终 SQL），因此仍需回归测试
- **Schema 不能轻易修改**：State Schema 是跨 Runtime / Node / Tool / Test 的数据契约；Context 组装规则依赖字段名与语义——改 Schema = 所有 Context 组装点同步修改

```mermaid
flowchart LR
    subgraph CTX["Model Context（组装产物，一次调用）"]
        P["Prompt（System Instruction 组件）"]
        S["State 切片"]
        T["Tool Result 摘要"]
        U["User Question"]
    end
    ST["Execution State（事实源）"] -. "切片" .-> S
    TR["Tool 输出"] -. "摘要" .-> T
    Q["用户请求"] -. "原样或规范化" .-> U
    PI["指令内容（可频繁迭代）"] --> P
    SC["Schema（数据契约，慎改）"] -. "决定切片结构" .-> S
```

## 3.6 Context Builder

Q8 的回答：**Context Builder 属于 Runtime Control Plane，是模型决策之前的组装步骤。**

在 architecture-map 总图中，它是 `Build Model Context` 这一步（Observe State 之后、Model Decision 之前）。它不属于：

- **模型**：模型不能构造自己的输入——它不知道自己的 Context 缺什么，除非 Runtime 告诉它（自引用不可能）
- **确定性策略层**：策略层做安全与治理决策（权限、终止）；Builder 做组装——但组装**受策略层约束**（例如敏感字段不进 Context）

```mermaid
flowchart LR
    O["Observe State"] --> B["Context Builder（Runtime Control Plane）"]
    Q["User Question"] --> B
    T["Tool Result 摘要"] --> B
    I["System Instruction"] --> B
    P["Deterministic Policy（过滤约束：敏感字段等）"] -. "约束组装" .-> B
    B --> D["Model Decision（一次调用）"]
```

本项目现状（如实说明）：`manual_agent_loop` 与 `basic_langgraph` 的 Demo **没有显式 Builder**——`FakeLLM` 直接读 State（`StateProxy` 即最简"视图"形态）。这是教学简化：Builder 的职责（选择切片、组装、过滤）在真实系统中显式存在；显式组装与 System Instruction 属于后续 Prompt Builder 章节（Q10）。

## 3.7 Context Contract

Q9 的回答：**不同 Runtime 生成一致 Context，依赖组装规则独立于 Runtime 载体。**

已有的事实基础（TASK-0003 已验证）：`GraphState` 与 `AgentState` 字段语义对齐——**State 契约不随 Runtime 变化**。推论：只要 Context Builder 从同一 State 契约按同一规则组装，两个 Runtime 生成的 Context 就一致。

组装规则作为契约，至少包含（本章只做解释性列举，不展开实现）：

- **输入源**：哪些字段进（3.3 的选择规则）
- **顺序**：指令 / 事实 / 结果的排列
- **过滤**：策略层约束下的排除规则（敏感字段、控制字段）

**注意**：本项目 Demo 未显式实现 Builder，因此"双 Runtime 生成一致 Context"是**推论**（由 State 契约一致性推出），不是已测试的事实——这是本章明确的边界，也是后续章节的实现目标。

## 3.8 常见误区

1. **"Context = Prompt"**：Prompt 是 Context 的指令组件；Context 还包括 State 切片、Tool 结果、用户问题（3.5）。
2. **"模型能看到 State"**：模型只能看到 Runtime 构造给它的那一次调用输入（3.1）；graph 版本连 State 字典本身都看不到，只有只读视图。
3. **"Context 越多越好"**：最小切片原则——控制字段与不相关事实不进 Context（3.3）；塞入越多，模型越容易把"展示性信息"误当决策依据。
4. **"Context 是长期存储"**：一次调用可见，调用结束即失效（3.4）；跨执行保留是 Memory 的职责（后续章节）。
5. **"Context Builder 是模型职责"**：组装是 Runtime Control Plane 的职责，模型不能构造自己的输入（3.6）。

## 3.9 总结

十个问题的浓缩答案：

| # | 问题 | 答案 |
|---|---|---|
| Q1 | 为什么模型永远看不到整个 Runtime？ | 模型的输入边界就是 Runtime 构造的那次调用；循环/校验/终止都不在模型可见范围 |
| Q2 | Context 是什么？为什么不是 State？ | 一次调用可见的组装产物；State 服务执行（跨轮），Context 服务调用（不跨轮） |
| Q3 | State 如何进入 Context？ | 只进影响本次决策的切片（user_question/current_sql/校验结果/执行摘要）；控制字段与不相关事实不进 |
| Q4 | Prompt 与 Context 是什么关系？ | Prompt 是 Context 的指令组件（System Instruction），不是 Context 本身 |
| Q5 | 为什么 Context 是一次调用可见？ | 生命周期=创建于调用前、失效于调用后；下一轮重新组装 |
| Q6 | 为什么 Context 可以变化而 State 不需要变化？ | Context 是组装产物（每轮可重建）；State 是事实源（只在写回时更新）——Context 变化是 State 演化的投影 |
| Q7 | 为什么 Prompt 可频繁修改、Schema 不能？ | Prompt 是 Context 的单个组件（行为策略，需回归）；Schema 是跨组件数据契约 |
| Q8 | Context Builder 属于哪一层？ | Runtime Control Plane（Observe 之后、Decision 之前）；受策略层过滤约束；不是模型职责 |
| Q9 | 如何保证不同 Runtime 生成一致 Context？ | 组装规则独立于 Runtime 载体，以 State 契约为依据（双 Runtime 一致性是推论，Demo 未显式实现 Builder） |
| Q10 | 与 Prompt Builder / Memory 的边界？ | 显式组装与 System Instruction → Prompt Builder 章节；跨执行检索 → Memory 章节；MCP / RAG → Part 6 |

**本章验收标准：**

- [ ] 能解释"模型只能看到 Runtime 构造给它的输入"及双 Demo 的证据（StateProxy 只读视图）
- [ ] 能区分 Context（一次调用）与 State（一次执行）
- [ ] 能列出 State → Context 的进入 / 不进入规则（最小切片）
- [ ] 能说明 Prompt 是 Context 的组件而非 Context 本身
- [ ] 能说明 Context 生命周期与"Context 变化是 State 演化的投影"
- [ ] 能说明 Builder 属于 Runtime Control Plane 及其两个"不属于"（模型、策略层）
- [ ] 能区分本章与 Prompt Builder / Memory / MCP / RAG 的边界

**本章边界**：Prompt Builder、Memory、Checkpoint、MCP、RAG、LangGraph API 均属后续章节（architecture-map 第 4 节归属表）；本章不定义新架构、不修改 principles / architecture-map / ADR。
