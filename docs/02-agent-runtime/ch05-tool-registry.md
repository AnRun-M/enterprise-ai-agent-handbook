# 第 5 章：Tool Registry——Runtime 如何管理可调用能力

> 状态：draft（2026-08-01）
> 前置阅读：第 1 章（Loop 中的 Act）、第 2 章（Tool Result 进 State）、第 3 章（Definition 与 Tool Result 摘要进 Context）、第 4 章（Builder 组装允许暴露的 Definition）、`.ai/principles/architecture-map.md`（第七层 Tool / External Systems）
> 本章回答：**Runtime 如何管理 Agent 可调用的能力？**
> 不展开：Tool Executor 生产实现、MCP 协议、Tool Retry / Timeout、Sandbox、LangGraph ToolNode、权限系统实现；不新增 Tool Demo。

**整章主线：**

> **Tool Registry 不是工具集合本身，也不是模型决策器。它是 Runtime 中管理"能力描述"和"执行映射"的注册表。模型看到的是 Tool Definition，Runtime 执行的是 Tool Handler，Registry 负责把二者对应起来。**

## 5.1 为什么需要 Tool Registry

从两个 Demo 出发（`examples/manual_agent_loop` 与 `examples/basic_langgraph` 的事实）：

- manual 版本的 `_dispatch(action, state)`（`runtime.py`）用显式分支处理 GENERATE_SQL / FIX_SQL / FINALIZE——工具数量少（Validator、Executor），分支有限，硬编码可维护
- graph 版本的节点（`nodes.py`）直接调用注入的 validator / executor——同样是小工具集的直接调用
- 两个 Demo 都**没有 Tool Registry**——这是事实，本章描述的是**规模增长后的 Runtime 抽象**，不是已实现状态（诚实标注）

真实系统里 Tool 数量增长后，硬编码 dispatch 会失控：

- `if/elif` 越来越长（每加一个 Tool 改一遍调度代码）
- Tool 定义散落各处（模型看到的描述与执行器实现分离漂移）
- schema 与执行器不同步（改了输入格式，模型还在生成旧参数）
- 测试困难（每个 Tool 的契约无法统一断言）
- 权限过滤困难（无法在"暴露给模型"这一层统一拦截）
- 不同模型协议适配困难（每个模型对 Tool 描述格式要求不同）

**Tool Registry 就是为这些问题而生的 Runtime 组件：把"能力描述"与"执行映射"集中管理。**

## 5.2 Tool Registry 的最小模型

概念结构（描述性，不锁定具体类名）：**ToolSpec**（能力描述）、**ToolHandler**（执行器）、**ToolRegistry**（注册表）。至少区分以下概念：

| 概念 | 承载什么 | 谁消费 |
|---|---|---|
| **Tool Name** | 唯一标识 | 模型（Tool Call 引用）、Runtime（查找） |
| **Canonical Tool Definition** | 能力描述的单一事实：name / description / input schema | 模型（经 Tool View）、Runtime（校验与文档） |
| **Input Schema** | 参数结构（字段、类型、约束） | 模型（生成参数）、Dispatcher（校验） |
| **Output Contract** | 结果结构约定（5.8） | Dispatcher（归一化）、State（摘要） |
| **Tool Handler** | 单个 Tool 的具体执行入口或业务适配器 | 仅 Dispatcher |
| **Metadata** | 版本、归属、成本、审计信息 | Runtime、审计 |
| **Deployment-level enabled / disabled** | 全局启停状态（Registry 内的稳定信息） | Registry 暴露时 |
| **Tool View** | 本次模型调用可见的 Definition 子集（请求级派生产物） | Prompt Builder（组装） |

**四个状态必须区分（请求级权限状态不得污染全局 Registry）：**

- **registered**：已注册（在 Catalog 中）
- **globally enabled**：全局启用（deployment 级）
- **available for this request**：本次请求可用（Request Context + Policy 计算）
- **exposed to model**：暴露给模型（Tool View 中的 Definition）

前两个属于全局 Registry（稳定）；后两个是**请求级派生产物，不回写全局 Registry**。

```mermaid
flowchart LR
    subgraph REG["Tool Registry / Catalog（稳定注册信息）"]
        SPEC["ToolSpec（canonical definition / input-output contract / handler binding / metadata / deployment enabled-disabled）"]
        MAP["name → handler binding 映射"]
    end
    subgraph REQ["Request Context + Policy（请求级）"]
        AV["可用性计算（user / tenant / role / session / request）"]
        VIEW["Tool View（Definition 子集，派生产物，不回写 Registry）"]
    end
    SPEC --> MAP
    MAP --> H["Tool Handler（业务执行）"]
    SPEC --> AV
    AV --> VIEW
    VIEW --> B["Prompt Builder（组装进模型请求）"]
```

## 5.3 Definition 与 Handler

**必须清楚区分（Q3 / Q4 / Q5 的回答）：**

- **Canonical Tool Definition**：给模型和 Runtime 描述"这个能力是什么、怎么调用"——name / description / input schema。**Registry 内维护的是 canonical definition（单一事实）**；不同模型协议格式（OpenAI / Anthropic / Gemini 等）由 **Provider / Protocol Adapter** 转换，不应产生多套独立业务定义（本章只说明边界，不展开具体供应商 API）
- **Tool Handler**：单个 Tool 的具体执行入口或业务适配器——`run_sql` Handler 可以选择 Athena、Spark 或 Trino **Execution Engine**，但 **Handler 不等于 Engine**

Text-to-SQL 例子：

- `run_sql` **canonical definition**：name="run_sql"、description="执行只读 SQL 并返回摘要"、input schema（sql: string, limit: int）
- `run_sql` **handler**：执行入口；底层可选 Athena / Spark / Trino / Database Engine

**模型只能消费 Definition（经 Tool View）；Runtime 才能调用 Handler。**

```mermaid
flowchart LR
    subgraph M["模型侧"]
        D["Tool Definition（name / description / input schema）"]
    end
    subgraph R["Runtime 侧"]
        H["Tool Handler（业务执行逻辑）"]
    end
    REG["Tool Registry"] --> D
    REG --> H
    D -. "模型只能消费描述" .-> M
    H -. "Runtime 才能调用执行" .-> R
```

**为什么必须分离（Q5）**：模型需要的是**描述**（可进 Context、可校验参数）；执行需要的是**实现**（绝不能进 Context——实现细节与安全边界）。分离使三件事成为可能：schema 独立演进（5.7）、多模型协议适配（由 Provider Adapter 转换 canonical definition，不产生多套业务定义）、安全边界清晰（Definition 可过滤，Handler 受保护）。

## 5.4 Registry 如何进入 Agent Loop

Tool Call 的完整路径（Q6 / Q7 的回答）：

```mermaid
flowchart LR
    B["Prompt Builder（第 4 章）"] --> TD["Tool View（允许暴露的 Definition 子集）"]
    TD --> C["Model Context"]
    C --> CALL["Model Tool Call（tool name / arguments / call id）"]
    CALL --> P1["Dispatcher Parse"]
    P1 --> P2["Input Schema Validation"]
    P2 --> P3["Authorization / Policy Check（即使未暴露也再次鉴权）"]
    P3 --> L["Registry Lookup（返回 handler binding / ToolSpec）"]
    L --> E["Dispatcher Invoke Handler"]
    E --> R1["Handler Result"]
    R1 --> N["Dispatcher Normalize"]
    N --> R["Tool Result Contract"]
    R --> S["State / Context（控制信息 / 摘要）"]
    S --> B
```

**强调**：模型决定 Tool Call（是否调用、调用哪个、生成什么参数——开放式语义决策，第 1 章 1.4）；**Registry 只负责 lookup，不自动执行 Handler**——它只返回 handler binding / ToolSpec；Dispatcher 持有解析、校验、鉴权、调用、错误边界与归一化的完整流程（5.5）。

Tool Definition 进入 Context 的路径依赖第 3/4 章：Builder 组装**允许暴露**的 Definition（ch04 4.6：Builder 执行、Policy 决定）；Tool Result 的控制信息进入 State（ch02 2.5）、摘要可回流下一轮 Context（ch03 3.2）。

## 5.5 Tool Dispatch

Tool Call 至少包含：**tool name、arguments、call id**。

**Tool Dispatcher**（单次 Tool Call 的 Runtime 调度组件）持有完整流程（Q7 的回答）：

1. **Parse**：从模型输出中提取 tool call
2. **Input Schema Validation**：arguments 是否符合 Input Schema
3. **Authorization / Policy Check**：即使 Tool 未暴露，模型伪造调用也必须再次鉴权
4. **Registry Lookup**：Registry 返回 handler binding / ToolSpec
5. **Invoke Handler**：执行 handler（超时 / 错误边界属 Tool Execution Infrastructure，后续章节）
6. **Normalize**：handler 结果归一化为 Tool Result Contract（5.8）

**四个概念必须拆清（不可混为一个）：**

| 概念 | 职责 |
|---|---|
| **Tool Registry / Catalog** | 保存稳定注册信息与查找映射（name → handler binding）；不自动执行 Handler |
| **Tool Dispatcher** | 单次 Tool Call 的调度流程（解析、校验、鉴权、调用、归一化） |
| **Tool Handler** | 单个 Tool 的具体执行入口或业务适配器（真正干活） |
| **Tool Execution Infrastructure** | timeout / retry / concurrency / sandbox / isolation / metrics 等后续生产能力（本章不展开） |
| **Execution Engine** | Athena / Spark / Trino / Database 等底层执行引擎（Handler 可选择，不等于 Handler） |

这和第 4 章"Policy 决定、Builder 执行"是同一类分工：**注册表不调度、调度器不执行业务、执行器不决定暴露什么**。

## 5.6 权限与可用性

Q8 的回答：**Tool Registry 不负责权限、安全和业务策略。** 请求级可用性由 **Request Context + Policy** 计算（user / tenant / role / session / request 等信息）；Registry 只保存全局注册与部署级启停状态。

分层：

- **registered / globally enabled**：全局 Registry（稳定，注册与部署级启停）
- **available for this request**：Request Context + Policy 计算（请求级）
- **exposed to model**：Tool View（派生 Definition 子集，**不回写全局 Registry**）

```mermaid
flowchart TD
    P["Request Context + Policy（请求级可用性计算：user / tenant / role / session / request）"] --> V["Tool View（暴露的 Definition 子集，派生产物）"]
    V --> C["Model Context（暴露前过滤）"]
    C --> CALL["Model Tool Call"]
    CALL --> D1["Dispatcher：Authorization / Policy Check（即使未暴露，伪造调用也再次鉴权）"]
    D1 --> E["最终受保护资源：不可绕过的执行边界再次执行授权或安全约束"]
    D1 -. "校验失败 → 拒绝（即使模型已调用）" .-> X["拒绝 / 错误结果"]
```

纵深防御三层：

1. **Context 暴露前过滤**：不允许的 Tool 不出现在 Tool View 里（模型"看不到"它）
2. **Dispatcher 再鉴权**：即使模型恶意或错误地调用了未授权 Tool，Dispatcher 仍校验并拒绝
3. **最终受保护资源边界**：**不强制所有 Handler 重复实现完整权限系统**——最终受保护资源必须在**不可绕过的执行边界**再次执行授权或安全约束，该边界可以是：Handler、Tool adapter、downstream service、database / IAM permission、SQL validator / read-only 执行账号

**Registry 的角色**：保存稳定注册信息；请求级可用性由 Request Context + Policy 计算——Registry 是**查找与暴露的执行通道**，不是策略的**制定者**（三层边界：策略属于确定性策略层，`.ai/principles/runtime-design.md`）。

## 5.7 Tool Schema 与版本

Q9 的回答：Tool schema 变化可能影响：

- 模型生成的参数（模型按旧 schema 生成 → 校验失败或错误调用）
- Prompt / Context（Definition 文本变化）
- Dispatcher 校验逻辑
- Handler 输入（结构变化）
- 测试（契约断言失效）
- 历史 Trace 重放（旧调用按新 schema 无法解释）

```mermaid
flowchart LR
    SC["Tool schema 变更"] --> A["模型生成参数"]
    SC --> B["Prompt / Context"]
    SC --> C["Dispatcher 校验"]
    SC --> D["Handler 输入"]
    SC --> E["测试断言"]
    SC --> F["历史 Trace 重放"]
```

区分两类变更：

- **兼容变更**：新增可选字段（旧调用仍可解释）
- **破坏性变更**：字段改名、类型变化、语义变化、删除字段（旧调用不可解释）

不强行规定 Semantic Versioning，但：**稳定系统必须有版本标识或兼容策略**——否则模型、Dispatcher、Handler、测试、审计五方各自漂移（第 2 章 2.8 的契约论证同样适用：Tool schema 是跨组件的契约）。

## 5.8 Tool Result Contract

Tool Result **不应随意返回任意对象**（Q7 的归一化部分）。采用**判别式语义**——成功态与失败态互斥、可编程判断（不锁定具体 JSON 类或字段名）：

**成功结果**：

- `status = success`
- `data`（结构化结果）
- `metadata / provenance`（来源、版本、耗时）
- `references`（可选引用：ID / URI / digest）

**失败结果**：

- `status = error`
- `error_code`（可编程处理的错误标识）
- `human-readable message`（给人看的说明）
- `retryable`（如适用）
- `metadata / provenance`

结合 Text-to-SQL：`run_sql` 的结果**不要把整个超大结果集直接塞进 State 或 Context**——优先返回：

- **row count**（行数）
- **columns**（列定义）
- **sample**（抽样行）
- **data_ref**（完整数据的外部引用）
- **query id**（可追溯）
- **digest / summary**（摘要）

这与第 2 章 2.6（State 不复制外部事实）、第 3 章 3.3（最小充分上下文）、第 4 章（引用策略）完全一致：**控制信息与摘要进 State / Context，完整数据留在外部**。

## 5.9 常见误区

1. **"Tool Registry = Python dict"**：dict 只有 name→object 映射；Registry 管理 Definition / Handler / Metadata / Availability / 版本与查找语义（5.2）。
2. **"Tool Registry 决定调用哪个 Tool"**：调用决策是模型的开放式语义决策；Registry 只回答"名字对应哪个执行器"（5.4）。
3. **"Tool Definition = Tool Handler"**：描述与实现必须分离——模型消费 Definition，Runtime 调用 Handler（5.3）。
4. **"Tool 注册后自动安全"**：注册只建立映射；权限与安全是策略层 + 纵深防御三层（5.6）。
5. **"所有 Tool 都应暴露给模型"**：暴露是 Policy 过滤后的 Tool View 子集（5.6）。
6. **"Tool Result 原样塞回 Context"**：必须归一化为 Output Contract，摘要进 State / Context，完整数据留外部（5.8）。
7. **"MCP = Tool Registry"**：MCP 是工具连接标准（TERMINOLOGY）；Registry 是 Runtime 内部的能力管理组件——两者是不同层（5.10 边界表）。
8. **"Registry 越动态越好"**：动态注册带来 schema 漂移与审计缺口；稳定系统需要版本标识与兼容策略（5.7）。

## 5.10 总结

十个问题的浓缩答案：

| # | 问题 | 答案 |
|---|---|---|
| Q1 | 为什么 Runtime 需要 Tool Registry？ | 工具增长后硬编码 dispatch 失控（if/elif 膨胀 / 定义散落 / schema 漂移 / 测试权限适配困难） |
| Q2 | 与普通 dict 有什么区别？ | dict 只有映射；Registry 管理描述、执行映射、元数据、可用性、版本与查找语义 |
| Q3 | Tool Definition 是什么？ | 能力描述：name / description / input schema——给模型和 Runtime 看 |
| Q4 | Tool Handler 是什么？ | 单个 Tool 的具体执行入口或业务适配器；可选底层 Execution Engine（Athena / Spark / Trino / Database），Handler ≠ Engine |
| Q5 | 为什么 Definition 与 Handler 必须分离？ | 模型只需要描述（可进 Context），实现绝不能进 Context；分离使 schema 演进 / 多协议适配（Provider Adapter）/ 安全边界可行 |
| Q6 | 模型如何知道有哪些 Tool？ | 经 Builder 组装的 Tool View（请求级允许暴露的 Definition 子集）进入 Model Context（ch03/ch04） |
| Q7 | Runtime 如何从 Tool Call 找到执行器？ | Dispatcher 完整流程：Parse → Schema Validation → Authorization / Policy Check → Registry Lookup → Invoke Handler → Normalize（Registry 只返回 binding，不自动执行 Handler） |
| Q8 | Registry 负责权限安全策略吗？ | 不制定；请求级可用性由 Request Context + Policy 计算（Tool View 派生产物，不回写 Registry）；纵深防御：暴露前过滤 / Dispatcher 再鉴权 / 最终受保护资源边界 |
| Q9 | Tool schema 变化为什么需要版本管理？ | 影响模型参数 / Context / 校验 / Handler / 测试 / Trace 重放；破坏性变更必须版本标识或兼容策略 |
| Q10 | 与 Prompt Builder / MCP / Handler 的边界？ | Builder=组装 Tool View 进 Context；MCP=工具连接标准（外部协议）；Handler=业务执行入口；Dispatcher=调度流程；Execution Infrastructure / Engine=后续生产能力与底层引擎；Registry=能力管理（注册 / 描述 / 映射 / 查找） |

**本章不会讨论什么**（边界声明）：Tool Execution Infrastructure 生产实现（timeout / retry / concurrency / sandbox / isolation / metrics）、MCP 协议、LangGraph ToolNode、权限系统实现、Provider Adapter 具体 API、新增 Tool Demo——均属后续章节或明确不在本书范围。

**本章验收标准：**

- [ ] 能复述本章主线（Registry = 能力描述与执行映射的注册表，不是工具集合、不是决策器）
- [ ] 能区分四个状态（registered / globally enabled / available for this request / exposed to model）与 Tool View 的请求级派生性质（不回写 Registry）
- [ ] 能区分 Tool Registry / Dispatcher / Handler / Execution Infrastructure / Execution Engine 五种职责
- [ ] 能说明 canonical definition 与 Provider Adapter 边界（不产生多套业务定义）
- [ ] 能画出 Dispatcher 完整调用路径（含 Authorization 步骤）并指出 Registry 只返回 binding
- [ ] 能说明权限纵深防御三层与"最终受保护资源边界"（不强制 Handler 重复实现完整权限系统）
- [ ] 能区分兼容 / 破坏性 schema 变更及其影响面
- [ ] 能说明判别式 Tool Result Contract 与 Text-to-SQL 的摘要引用策略（与 ch02/03/04 一致）
- [ ] 能诚实标注 Demo 未实现 Registry（架构抽象）

**与前三章的关系**（引用不复制）：Tool Call 是 Loop 中的 Act（ch01 1.2）；Tool Result 控制信息进 State（ch02 2.5）；Definition 与 Result 摘要可进 Context（ch03 3.2-3.3）；Builder 组装允许暴露的 Definition（ch04 4.6）。
