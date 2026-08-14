# TASK-0034：T02 意图与语义解析（Gate A：Architecture / Contract）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-13 |
| Updated | 2026-08-13 |
| Related ADR | ADR-0004（模型输出概率性；本任务定义模型推断 ≠ 外部事实） |
| Related Task | TASK-0029（T02 = Wave 2 候选，IntentResult Proposed）、TASK-0032（T01）、TASK-0033（T03） |
| Related Example | examples/text2sql_state（默认载体，Gate B 落地） |
| Related Principle | architecture-map（Model Context / External Source of Truth / 引用策略） |

## 定位

**Gate A：Architecture / Contract 冻结**。只冻结 T02 的语义边界与 contract 决策，**不写 implementation**（无 examples / tests / Chapter 正文）。与 T01/T03 同模式：**Gate A 冻结语义 contract；Python 类型 / 字段名 / 内部表示在 Gate B 落地，不得改变已冻结语义边界；若实现需要改变这些边界，必须返回 Architecture Review，不得在 Gate B 自行重定义 contract。** TASK-0029 已把 T02 的 Proposed contract 命名为 **IntentResult**（`TASK-0029`：IntentResult ← T02；ch20 边界："它不是 IntentResult、不是 T02 最终 schema"）——本 Gate A 沿用该命名，不引入新名称。

## 一、固定主线（逐字冻结）

> **"T02 将 T01 产生的 normalized_question 解释为后续 Runtime 可以显式消费的结构化语义解释与意图；它负责 semantic interpretation，但不负责生成 SQL、不读取权威 metadata、不做权限风险裁决，也不把模型推断结果伪装成外部事实。"**

固定原则（Review 修正新增）：

> **"Semantic interpretation is structured inference, not authoritative fact."**

（结构化语义解释仍然是推断结果，不因结构化而获得事实地位。）

输入：`normalized_question`（T01 产物）。输出：semantic / intent contract（**IntentResult**）。下游：T03 retrieval criteria、T04 SQL generation、可能的 clarification / failure control flow。本轮只冻结 contract。

**术语约定（Review 修正）**：T02 的产出（IntentResult / semantic candidates / semantic interpretation）**不得称为 fact / semantic fact / structured fact**——除非在否定或对比上下文（如"不是 authoritative fact"）。"fact" 表述只属于 T03 的 authoritative facts。

## 二、T01 / T02 边界

| | T01（representation normalization） | T02（semantic interpretation） |
|---|---|---|
| 职责 | trim / whitespace canonicalization / empty detection | 识别 metric / dimensions / entities / time range / filters / aggregation intent / query intent |
| 产物 | normalized_question | IntentResult（semantic / intent contract） |

固定原则：

> **"Normalization changes representation; semantic parsing interprets meaning."**

**不得把 T01 职责重新搬进 T02**：T02 假定输入已是 normalized 形式（空输入由 T01 在 lifecycle 层处理）；T02 不做 whitespace canonicalization、不重复 empty detection。

## 三、T02 / T03 边界（Gate A 重点）

- **T02 产生**：structured semantic interpretation 以及 source-agnostic retrieval requirements（"用户想查 GMV"）；source-specific RetrievalCriteria 由 integration / source-specific adapter 产生
- **T03 产生**：authoritative facts（"GMV = paid_amount − refund"——来自 External Source of Truth）

固定原则：

> **"Semantic interpretation may identify what facts are needed; it must not manufacture authoritative facts."**

（语义解释可以识别需要哪些事实；不得制造权威事实。）

T02 可以推断用户想要哪个 metric / dimension / entity 的**语义候选**；但 metric 定义、region mapping、业务口径、canonical rule **必须来自 T03 权威源**。T02 输出始终属于 **structured inference**，不是 **authoritative fact**；其中既可以包含 **resolved interpretation**，也可以包含 **ambiguous candidates**。

## 四、LLM 的角色

T02 是未来 Model Decision 挂载点，但必须区分：

| | Model-derived interpretation | Authoritative business fact |
|---|---|---|
| 可输出 | metric candidate / dimension candidate / time expression interpretation / intent classification | ✗ 禁止 |
| 不可成为 | — | schema source / metric definition source / permission source / business-rule authority |

**不得因为使用 LLM 就把结果称为"事实"**。模型输出属于 interpretation（structured inference，非 authoritative fact），其中可以包含 resolved interpretation 或 ambiguous candidates；只有经 T03 权威检索确认的内容才具有事实地位。Gate A 冻结：T02 的 output contract 必须显式表达 interpretation 性质（resolved / candidate / unresolved / not-applicable 四语义状态可区分，见第八节），不得以 facts 自居。

## 五、Contract 设计方案比较

至少比较三种方案：

- **A. 直接增加多个 State fields**（metric / dimensions / entities / time_range / filters ...）
- **B. 独立 IntentResult / SemanticResult 对象**（单字段承载）
- **C. Typed semantic contract + State channel**（强类型语义契约 + 独立 State 通道）

| 维度 | A. 多个 State fields | B. 独立 IntentResult 对象 | C. Typed contract + 单 State channel |
|---|---|---|---|
| ownership | 碎片化（多字段多属主，难收敛到单一 T02-owned） | 单一 T02-owned | 单一 T02-owned ✅ |
| downstream consumers | 下游需读多个字段、自拼语义 | 单对象消费 | 单对象消费（adapter / T04 接口明确）✅ |
| optionality | 多可选字段 → State 膨胀、Optional 组合爆炸 | 单可选字段 | 单可选字段 ✅ |
| evolution | 加类别 → 改 State schema（跨 Task 影响） | 对象内部演进 | 对象内部演进（State 通道不变）✅ |
| testability | 逐字段断言、易漏 | 整对象相等测试 + outcome 测试 | 整对象相等测试 + outcome 测试 ✅ |
| serialization | 多字段 | 单对象（可序列化，进 State / Trace） | 单对象 ✅ |
| Graph State size | 5+ 字段 | 1 字段 | 1 字段 ✅ |
| T03 fixture replacement | 直接映射（与 fixture key 绑定） | adapter 解耦 | adapter 解耦 ✅ |
| T04 consumption | 碎片化（T04 要自拼 intent） | 携带完整 semantic intent | 携带完整 semantic intent ✅ |
| ambiguity representation | 需逐字段 ambiguity 标志 | outcome + 对象内候选表示 | outcome + 对象内候选表示 ✅ |
| backward compatibility | 多新可选字段 | 一个新可选 channel（additive） | 一个新可选 channel（additive）✅ |

**不要因为 T03 当前有 RetrievalCriteria 就直接把它升级成 T02 最终 schema**。RetrievalCriteria 是 T03 当前的 **source-specific fixture**，不是 T02 final semantic contract；**T02 不直接生成 RetrievalCriteria**。具体 source lookup representation 由 integration / source-specific adapter 根据 source-agnostic retrieval requirements 映射得到（第十三节方案 2 决策）。

## 六、推荐 Contract 决策

**采用方案 C（typed semantic contract + 单 State channel），实现形态为独立 IntentResult 对象**（B 的形状 + C 的通道语义，命名与 TASK-0029 Proposed 一致）。

- 语义类别冻结（教学规模）：**metric candidates / dimensions / entities / time range（semantic time expression）/ filters / aggregation intent / query intent**
- IntentResult 作为 **T02-owned derived state**，以**单个 State channel** 进入 `Text2SQLState`（字段名 Gate B 落地；仍为教学规模选择——可序列化纯数据，不保存 model client / handle）
- 具体字段结构与类型在 Gate B 落地，**不得改变本节冻结的语义类别边界**

## 七、Ambiguity 设计

T02 不能只有 success / failure。例："销售额"可能对应 GMV / paid amount / net revenue——这**不是** metadata NOT_FOUND，**不是** source UNAVAILABLE，而是 **semantic ambiguity**。

**双层区分，不混成一个字段：**

| 类型 | 属主 | 含义 | 表达 |
|---|---|---|---|
| **interpretation ambiguity** | T02 | 用户话语存在多个合理解读（同一话语 → 多个语义候选） | T02 outcome（AMBIGUOUS）+ 对象内候选表示 |
| **authoritative-source ambiguity** | T03 | 已解析 key 在权威源中有多个合法候选 | T03 现有 AMBIGUOUS 五态（保持不变） |

边界例：interpretation 无歧义（"查询 GMV"）但 source 有多候选 → 这是 **T03 AMBIGUOUS**；interpretation 本身有歧义（"销售额"）→ **T02 必须显式暴露**，不得静默选择候选。

**T02 自己不得把 ambiguity 伪装成 resolved fact**。后续 **application policy** 可以选择：clarification / human input / deterministic domain rule / 在适用场景通过 T03 authoritative facts 对候选做验证与消歧——但这是 policy 决策，不是 T02 的自动行为。T02 不得把 interpretation ambiguity 映射为 T03 的 NOT_FOUND / UNAVAILABLE。

固定原则：

> **"T02 exposes ambiguity; it does not unilaterally resolve it."**

**AMBIGUOUS 后续边界（Review 修正新增）**：AMBIGUOUS 可以产生 candidate-scoped retrieval requirements（如"需要验证哪些候选是正式企业指标"），但**不能因此自动进入 T03**。后续 policy 可选择：① clarification ② human input ③ deterministic domain rule ④ T03-assisted disambiguation——因此 **ambiguous outcome ≠ routing decision**。

## 八、Failure / Outcome Contract

**不机械复制 T03 五态**——T02 是 semantic interpretation，T03 是 authoritative retrieval，Outcome taxonomy 可以不同。

| 情况 | 类别 | 表达 |
|---|---|---|
| complete interpretation（**当前 query intent 所需 semantic requirements 均已充分表达——不要求所有可选语义类别都有值**） | **expected application outcome** | COMPLETE |
| partial interpretation（已有部分有效 interpretation，但**至少一个当前请求所需**的 semantic requirement 未解析完成，如 metric 已定、time expression 未解析） | **expected application outcome** | PARTIAL |
| ambiguous interpretation（存在多个合理 interpretation candidates，T02 不静默选择） | **expected application outcome**（语义层） | AMBIGUOUS |
| unsupported request（请求不属于当前 T02 支持的 semantic capability，如"帮我删除数据"） | **expected application outcome**（→ clarification control flow） | UNSUPPORTED |
| invalid semantic input（normalized_question 为 None / 契约外输入） | **consumed-contract violation** | ValueError（不进入 outcome taxonomy）；normalized_question=None 可作为 T02 Node / parser 的 consumed-contract violation 代表，但 **pure parser 可接收 `str`，由 Node adapter 保证输入满足契约**——不强制所有内部函数接受 Optional[str] 再检查 None |
| model invocation / output-contract failure（transport / provider / authentication / configuration / malformed typed output / model refusal / unavailable output） | **不属于 semantic outcome taxonomy** | 不属四态；具体 failure classification / retryability / retry policy 留后续 failure / retry contract；**不在 Gate A 默认所有 model failure 都 transient** |
| runtime exception | **programming error** | 异常传播 |

**冻结：T02 outcome taxonomy = COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED 四态**（教学规模）。**不要全塞 failure_reason**——四类 expected outcome 各自表达语义，只有 consumed-contract violation 抛 ValueError。**invalid consumed input ≠ semantic outcome。**

**Outcome taxonomy 最终定义（Review 修正冻结）：**

- **COMPLETE**：当前请求所需 semantic requirements 已完整表达
- **PARTIAL**：有有效 interpretation，但至少一个 required semantic requirement 未解析
- **AMBIGUOUS**：存在多个合理 interpretation candidates，T02 不静默选择
- **UNSUPPORTED**：请求不属于当前 T02 支持的 semantic capability，但这是 expected application outcome

**四者都必须产生完整 IntentResult。** None 不表示任何 expected outcome。

**Applicability / unresolved 语义边界（Review 修正新增）：** IntentResult 必须能够区分：① semantic category **不适用于当前请求**（not applicable）② semantic category 对当前请求 **required 但尚未解析完成**（required but unresolved）——否则 PARTIAL 无法可靠判断。Gate A **不强行设计所有 Optional 字段**，只冻结语义能力；具体 Python representation 在 Gate B 落地。

固定原则：

> **"Optional semantic field absence is not automatically partial interpretation."**

（可选语义字段缺省 ≠ 自动 partial interpretation。）

**Resolved / Candidate / Unresolved / Not-applicable 语义状态（Review 修正新增）：** Gate A 不冻结具体 Python 字段，但 IntentResult 必须能够表达四种**可区分**的语义状态：

1. **resolved interpretation**——语义已唯一确定（如 metric 已确定）
2. **ambiguous candidates**——存在多个合理候选
3. **required but unresolved**——当前请求需要，但尚未解析
4. **not applicable**——当前 query intent 根本不需要该 semantic category

否则 COMPLETE / PARTIAL / AMBIGUOUS 无法可靠判定。**语义类别统一表述为 `semantic interpretations（resolved or candidate）`** 或 `semantic selections / candidates`——**不要让 Gate B 误以为所有已解析语义永远只是 candidates**；具体 Python 字段名留 Gate B，Gate A 只冻结四种语义状态可表达。

**Outcome → Retrieval Requirement Eligibility（Review 修正冻结）：** 不同 outcome 是否允许产生 retrieval requirements、是否自动进入 T03，Gate A 现在冻结：

| Outcome | Retrieval requirement eligibility | 是否自动进入 T03 |
|---|---|---|
| COMPLETE | 可表达当前请求需要的 source-agnostic retrieval requirements | **否**——由 application policy 决定 |
| PARTIAL | 可表达：① 已识别出的 retrieval needs ② 为补齐 unresolved required semantics 所需的 authoritative facts；**不得假装 interpretation 已 complete** | **否**——由 application policy 决定 |
| AMBIGUOUS | 可表达 candidate-scoped / disambiguation-oriented retrieval requirements（例："需要验证 GMV / paid amount / net revenue 哪些是正式企业指标"） | **否**——是否调用 T03 由 application policy 决定（见第七节） |
| UNSUPPORTED | **默认不产生普通 downstream retrieval requirements**（请求不属于当前支持的 semantic capability）；若未来某类 unsupported request 需要事实辅助重新分类，必须**单独设计**，不要在 Gate B 自动生成 | 否 |

**"retrieval requirements exists" ≠ "routing to T03 verified"。**

## 九、Original / Derived ownership

保持并应用 T01 已沉淀原则：

- `user_question` = **original**
- `normalized_question` = **T01-owned derived**
- T02 新产出的 semantic contract（IntentResult）= **T02-owned derived state**

> **"Field write capability ≠ field ownership."**
> **"Invalidate stale state according to field ownership and transition authority."**

**如果 T02 写 shared status / failure_reason，必须单独做 transition-authority Review**。**不要默认复制 T01 的 RUNNING → FAILED 规则。** Gate A 决策（见第十九节第 9 项）：T02 Node 默认**不写** status / failure_reason——语义层 outcome（四态）不是 Agent lifecycle，路由 / 澄清 / 终止属于后续 application control flow（与 T03"Outcome ≠ Agent lifecycle"连续）。

## 十、Stale semantic state（Gate A 预先回答）

上一轮 `metric = GMV`，本轮问题变成"昨天订单数"——旧 metric / dimension / filter 如何失效？

**Gate A 决策：T02 拥有整体 IntentResult，以整体 overwrite 天然避免多字段 stale state**（LangGraph 默认 overwrite 语义：不在 update 中返回字段 = 保留旧值；返回完整新 IntentResult = 整体替换所有旧子值）。**不需要逐字段 invalidation contract**——这是方案 C 相比方案 A 的决定性优势。

**每次正常完成 semantic interpretation——无论 outcome 是 COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED——都返回新的完整 IntentResult，整体 overwrite 上一轮 IntentResult**（上一轮 COMPLETE → 本轮 UNSUPPORTED：新 UNSUPPORTED IntentResult 整体替换旧结果，**不通过 `intent_result: None` 表达 expected outcome**）。

固定原则：

> **"Expected semantic outcomes always produce an IntentResult."**
> **"None means no valid T02 semantic result exists; it is not the representation of UNSUPPORTED."**

（expected semantic outcomes 总是产生 IntentResult；None 表示不存在合法 T02 semantic result，不是 UNSUPPORTED 的表示。）

`None` 只可能在**根本没有合法 semantic result** 时出现——具体包括哪些 failure path、Node 是否写 None，留 **Gate B failure-boundary Review**；不得把 infrastructure / model failure 混进 expected outcome。与 T01 的 stale-invalidation 模式（failure 显式失效 derived）保持同构，但**只适用于真正的 None path，不适用于四态 expected outcomes**。

## 十一、Time semantics 边界

用户表达"昨天 / 上个月 / 最近 7 天"：

- **T02 可解析为 semantic time expression**（如 `yesterday` / `last_month` / `last_7_days` 语义 token）——这是 interpretation
- **timezone / business calendar / fiscal calendar / data freshness cutoff** 可能来自 application / runtime facts 或 authoritative source——**T02 不得静默猜测**

Gate A 冻结：T02 输出 semantic time expression token，**不解析到具体日历时点**；日历 / 时区 / 新鲜度裁决属外部事实，具体落地在 T02 → T03 integration 时决策（Time 的 resolved 形式是否需要 T03 facts 参与，留 integration 边界）。

## 十二、Filter / Entity semantics 边界

"华东 / VIP 用户 / 已支付订单"：

- **T02 可识别 entity / filter intent**（语义 token：region entity / user-segment filter / status filter）
- **不能直接创造**：region mapping（华东 = 上海/江苏/...）、VIP rule、paid-status canonical rule——这些**可能需要 T03 retrieval**（如 fixture 的 `region.east_china` 事实）

推荐链路（冻结）：

```
normalized_question → semantic intent (IntentResult) → retrieval requirements → T03 authoritative facts
```

## 十三、T02 → T03 真实接口

T03 当前 `RetrievalCriteria` 明确是 **Proposed fixture**。本轮决策：

| 方案 | 内容 | 评估 |
|---|---|---|
| 方案 1 | T02 最终直接产 RetrievalCriteria | ❌ T02 被 T03 当前 fake source key 反向绑定；T03 fixture 演化会反向改变 T02 contract |
| 方案 2（推荐） | T02 产 **IntentResult** → source-agnostic retrieval requirements → **integration / source-specific adapter** → RetrievalCriteria（由 metric / dimension / entity / filter intent tokens 经逻辑契约层推导 source-specific 检索 keys） | ✅ semantic interpretation ≠ retrieval query representation；T02 不被 fixture 反向绑定；adapter 可独立单测 |

**Gate A 决策：方案 2，并细化为三层**（Review 修正）。固定原则升级为：

> **"Semantic interpretation ≠ retrieval requirement ≠ source-specific retrieval criteria."**

```
IntentResult（semantic interpretation）
    ↓
source-agnostic retrieval requirements（逻辑契约层，不绑定任何 source vocabulary）
    ↓
integration / source-specific adapter
    ↓
T03 RetrievalCriteria（Proposed fixture / source-specific query representation）
```

示例：IntentResult（metric candidate = GMV；region intent = 华东）→ source-agnostic requirement（need metric definition for GMV；need region mapping for 华东）→ 最后一层才落到具体 fake source lookup keys（`gmv` / `region.east_china`）。**最后一层属于 integration / source-specific adapter，不是 T02 semantic parser 自己的业务语义。**

- **RetrievalCriteria 继续保持 fixture 身份**（Proposed / source-specific query representation），**不升级为 T02 final semantic contract**；T03 fake source key vocabulary **不得进入 IntentResult**
- **Gate A 不强制创建 `RetrievalRequirement` Python DTO**——source-agnostic retrieval requirement 是**逻辑 contract layer**：Gate B 决定它作为 IntentResult 内部字段 / 独立 typed value / adapter 输入 view，但 **Gate B 不得删除这一层**

**Retrieval Requirement ≠ Routing（Review 修正新增）：**

> **"Retrieval requirement is data, not routing."**
> **"Having retrieval requirements does not authorize T02 to invoke T03."**

（检索需求是数据契约，不是路由指令；T02 能描述需要哪些权威事实，不等于 T02 决定现在执行 T03。）

T02 只产生 IntentResult / retrieval requirement data。T02 **不负责**：调用 T03 / route 到 T03 / retry T03 / clarification routing / terminate graph——这些由 **application control flow / Node / Edge / Command / Runtime** 表达。

## 十四、T02 → T04 边界

T04 SQL Generation 未来需要 **semantic intent + T03 trusted facts**：

- IntentResult 承载用户的 semantic intent（metric / dimension / time / filter 语义）
- T03 提供 authoritative facts
- T04 = 基于两者的生成

**T02 Contract 不应只为 T03 服务**——这是不把 T02 简单等同 RetrievalCriteria 的根本原因（第十三节方案 1 的否决理由在此复述：T04 消费 semantic intent，不是消费检索查询）。T04 仅建立接口位置，不实现。

## 十五、确定性与 Model Decision

- **不承诺 deterministic model output**（模型输出概率性，ADR-0004）
- **可以要求**：typed output contract / validation / normalization / bounded outcome taxonomy（四态封顶）
- **测试优先**：deterministic fake semantic parser 或 fixture——先验证 Contract；**Gate B 第一版不直接接真实 LLM**

## 十六、Evidence Planning（四列制）

| 类别 | 内容 |
|---|---|
| **已有证据** | T01 `normalized_question`（TASK-0029 Proposed NormalizationResult 在 Gate B 以简化字段落地——T02 IntentResult 同理可按语义类别落地）；T03 `RetrievalCriteria` fixture（Proposed）；T03 trusted retrieval contract（五态 / fact-level binding）；TASK-0029 IntentResult Proposed |
| **需要新增** | T02 unit evidence（deterministic fake parser）；semantic ambiguity（interpretation vs authoritative-source）；stale-state invalidation（整体 overwrite + failure None）；IntentResult → source-agnostic retrieval requirements → RetrievalCriteria（三层 adapter 链路）；T01 → T02 integration |
| **尚不能验证** | 真实 LLM interpretation quality；production multilingual semantic parsing；真实 business ontology；T03 → T04；full compiled graph；e2e |

## 十七、Integration Closure 设计（edge-scoped）

T02 进 main 后，**不要笼统宣布 T01 / T03 Integration closed**。按 capability edge 记录：

```
T01 → T02 IntentResult                                   （edge-scoped：deferred / closed）
IntentResult → source-agnostic retrieval requirements    （edge-scoped：deferred / closed）
retrieval requirements → source-specific RetrievalCriteria（edge-scoped：deferred / closed）
RetrievalCriteria → T03 RetrievalResult                  （edge-scoped：deferred / closed）
T03 RetrievalResult → T04                                （edge-scoped：deferred / closed）
compiled graph                                           （edge-scoped：deferred / closed）
real source                                              （edge-scoped：deferred / closed）
```

固定表述（加入本文件与 current.md planning）：

> **"Integration evidence is edge-scoped, not task-wide."**

（Integration 证据按 capability edge 记录，不是 task 级整体声明。）

**不要用一句 "T02 → T03 closed" 掩盖中间的 adapter contract**——未来 closure 必须按逻辑 edge 逐条记录。Gate A 只记录逻辑 edge，**不创建额外 TASK**。

**data edge ≠ routing edge（Review 修正新增）**：**"retrieval requirements exists" 不代表 "routing to T03 verified"**——edge 记录的是数据契约连接（IntentResult → requirements → RetrievalCriteria → RetrievalResult），不是 T02 拥有调用 / 路由 T03 的权限（第十三节 Retrieval Requirement ≠ Routing）。

## 十八、Gate A 最终决策（10 项，不得留"Implementation 时再看"）

| # | 决策 | 结论 |
|---|---|---|
| 1 | T02 output 的性质 | **IntentResult = structured semantic interpretation，不是 authoritative fact**——"Semantic interpretation is structured inference, not authoritative fact."；T02 产出（IntentResult / semantic candidates / interpretation）不得称为 fact（除否定 / 对比上下文） |
| 2 | Expected outcomes 是否都返回 IntentResult | **是**——COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED 四者都产生**完整** IntentResult（outcome 承载于对象内）；None 只表示"不存在合法 T02 semantic result"，**不是 UNSUPPORTED 的表示**；"Expected semantic outcomes always produce an IntentResult." |
| 3 | COMPLETE / PARTIAL 判定 | **基于当前请求 required semantic requirements**：COMPLETE = required 均已充分表达（**不要求所有可选类别有值**）；PARTIAL = 至少一个 required requirement 未解析；"Optional semantic field absence is not automatically partial interpretation." |
| 4 | 语义状态可区分性 | **resolved / ambiguous candidates / required but unresolved / not applicable 四态可区分**——否则 COMPLETE / PARTIAL / AMBIGUOUS 无法可靠判定；语义类别表述为 semantic interpretations（resolved or candidate），不暗示"所有已解析语义永远只是 candidates"；字段名 Gate B |
| 5 | IntentResult 与 RetrievalCriteria 关系 | **三层**：IntentResult → source-agnostic retrieval requirements → source-specific RetrievalCriteria；"Semantic interpretation ≠ retrieval requirement ≠ source-specific retrieval criteria."；RetrievalCriteria 保持 fixture / source-specific 身份，不升级为 T02 contract；fake source key vocabulary 不得进入 IntentResult；retrieval requirements 是逻辑层，Gate B 决定形态但**不得删除** |
| 6 | Outcome → retrieval eligibility | **已冻结**：COMPLETE 可表达所需 requirements；PARTIAL 可表达已识别 needs + 补齐 unresolved 所需 facts（不假装 complete）；AMBIGUOUS 可表达 candidate-scoped / disambiguation-oriented requirements；**UNSUPPORTED 默认不产生普通 downstream retrieval requirements**（未来需要必须单独设计，不在 Gate B 自动生成）；"retrieval requirements exists" ≠ "routing to T03 verified" |
| 7 | retrieval requirement 的性质 | **data，not routing**——"Retrieval requirement is data, not routing." / "Having retrieval requirements does not authorize T02 to invoke T03."；T02 不调用 / route / retry T03、不 clarification routing、不 terminate graph |
| 8 | ambiguity 的后续 | **暴露不消歧**："T02 exposes ambiguity; it does not unilaterally resolve it."；AMBIGUOUS 可产生 candidate-scoped requirements 但**不自动进入 T03**；downstream policy 决定 clarification / human input / domain rule / T03-assisted disambiguation；ambiguous outcome ≠ routing decision |
| 9 | lifecycle / routing authority | **T02 默认都不拥有**——不写 status / failure_reason（Outcome ≠ Agent lifecycle，同 T03，不复制 T01 RUNNING→FAILED）；不拥有 routing authority（调用 / 路由 T03 属 application control flow / Node / Edge / Command / Runtime）；未来需要 lifecycle transition 必须单独 transition-authority Review |
| 10 | Integration evidence edge-scoped | **"Integration evidence is edge-scoped, not task-wide."**——T01→IntentResult / IntentResult→retrieval requirements / requirements→RetrievalCriteria / RetrievalCriteria→T03 RetrievalResult / RetrievalResult→T04 / compiled graph / real source 各自 deferred / closed；**data edge ≠ routing edge**（"retrieval requirements exists" ≠ "routing to T03 verified"） |

## 十九、禁止事项（本轮）

- T02 implementation（examples / tests）
- 真实 LLM
- T04 implementation
- T06 / T07
- 修改 T01 / T03 / T05 implementation
- ROADMAP / content-map / Chapter 正文 / ADR / principles / architecture-map / Pattern Backlog（TASK-0031）

只允许：`TASK-0034`、`current.md`、规划 PR Description。

## 二十、验收标准（Gate A 阶段）

- [x] 固定主线逐字冻结（**结构化语义解释与意图**，非"结构化语义事实"；不生成 SQL / 不读权威 metadata / 不做权限裁决 / 不伪装事实；"Semantic interpretation is structured inference, not authoritative fact."）
- [x] 术语约定（T02 产出不得称为 fact / semantic fact / structured fact，除非否定 / 对比上下文；"fact" 表述只属 T03 authoritative facts）
- [x] T01 / T02 边界（representation vs interpretation；"Normalization changes representation; semantic parsing interprets meaning."）
- [x] T02 / T03 边界（semantic requirements vs authoritative facts；"must not manufacture authoritative facts"）
- [x] LLM 角色（Model-derived interpretation ≠ Authoritative business fact；candidate 性质显式）
- [x] Contract 方案比较（A / B / C × 11 维度）→ 方案 C 决策
- [x] Ambiguity 双层（interpretation vs authoritative-source，不混字段）
- [x] Outcome taxonomy（四态 expected outcomes / consumed-contract violation / model failure / runtime exception 分类明确；不机械复制 T03 五态）
- [x] **UNSUPPORTED 不以 None 表达**（四态都返回完整 IntentResult；"Expected semantic outcomes always produce an IntentResult."；"None means no valid T02 semantic result exists; it is not the representation of UNSUPPORTED."）
- [x] **COMPLETE / PARTIAL 基于 required semantics**（COMPLETE 不要求所有可选类别有值；PARTIAL = 至少一个 required requirement 未解析；"Optional semantic field absence is not automatically partial interpretation."）
- [x] **applicability / unresolved 可区分**（not applicable vs required but unresolved；Gate A 只冻结语义能力，字段 Gate B 落地）
- [x] **resolved / candidate / unresolved / not-applicable 四语义状态可区分**（否则 COMPLETE / PARTIAL / AMBIGUOUS 不可靠；语义类别表述为 semantic interpretations（resolved or candidate），不暗示"永远只是 candidates"）
- [x] **Outcome → Retrieval Requirement Eligibility 冻结**（COMPLETE / PARTIAL / AMBIGUOUS 各自 eligibility；UNSUPPORTED 默认不产生普通 downstream retrieval requirements；"retrieval requirements exists" ≠ "routing to T03 verified"）
- [x] **Retrieval Requirement ≠ Routing**（"Retrieval requirement is data, not routing."；T02 不调用 / route / retry T03、不 clarification routing、不 terminate graph——属 application control flow / Node / Edge / Command / Runtime）
- [x] **AMBIGUOUS 后续边界**（可产生 candidate-scoped requirements 但不自动进 T03；policy 四选项；ambiguous outcome ≠ routing decision）
- [x] Ownership（IntentResult = T02-owned derived；Field write capability ≠ ownership）
- [x] Stale semantic state（整体 overwrite；每次正常 interpretation 含 UNSUPPORTED 都整体替换；None 仅限无合法 result 的 failure path，留 Gate B failure-boundary Review）
- [x] Time / Filter / Entity 边界（semantic token vs external facts；推荐链路）
- [x] T02 → T03 **三层接口**（IntentResult → source-agnostic retrieval requirements → source-specific adapter → RetrievalCriteria；"Semantic interpretation ≠ retrieval requirement ≠ source-specific retrieval criteria."；RetrievalCriteria 保持 fixture；不强制 RetrievalRequirement DTO，Gate B 不得删除逻辑层）
- [x] **ambiguity 暴露不消歧**（"T02 exposes ambiguity; it does not unilaterally resolve it."；后续 application policy 决定 clarification / human input / domain rule / T03 facts 验证）
- [x] **model failure 收窄**（不属于 semantic outcome taxonomy；retryability / retry policy 未冻结；不默认全部 transient）
- [x] **consumed-contract violation 边界**（pure parser 可接收 str，Node adapter 保证输入契约；invalid consumed input ≠ semantic outcome）
- [x] T02 → T04 边界（IntentResult 不只服务 T03）
- [x] 确定性策略（fake parser 优先；typed contract + bounded taxonomy；第一版不接真实 LLM）
- [x] Evidence Planning 四列制（已有 / 需新增 / 尚不能验证）
- [x] Integration Closure edge-scoped（"Integration evidence is edge-scoped, not task-wide."）
- [x] Gate A 决策 10 项全部给出明确结论
- [x] Gate A Architecture Review：**APPROVED**（final consistency cleanup 完成；等待最终 Merge 确认）

## Review Focus（Gate A 最终 Architecture Review：APPROVED——以下为最终复审清单）

1. T02 output 是否仍被称为 fact（语义解释 ≠ authoritative fact）
2. IntentResult 是否明确属于 structured inference（"Semantic interpretation is structured inference, not authoritative fact."）
3. UNSUPPORTED 是否仍返回完整 IntentResult
4. COMPLETE / PARTIAL 是否基于 required semantics
5. resolved / candidate / unresolved / not-applicable 是否可区分
6. retrieval requirements 是否 source-agnostic
7. retrieval requirements 是否被错误当成 routing（"Retrieval requirement is data, not routing."）
8. AMBIGUOUS 是否自动调用 T03（应否：由 application policy 决定）
9. UNSUPPORTED 是否错误生成普通 RetrievalCriteria（应否：默认不产生普通 downstream retrieval requirements）
10. Integration 是否真正 edge-scoped（data edge ≠ routing edge；不用一句 "T02→T03 closed" 掩盖 adapter contract）

## 完成记录

- 2026-08-13：任务创建（in_progress，planning/t02-intent-semantic-contract 分支）。Gate A 草案完成：固定主线 / T01-T02 / T02-T03 边界 / LLM 角色 / Contract 方案比较（A/B/C × 11 维度）→ 方案 C / Ambiguity 双层 / Outcome taxonomy 四态 / Ownership 与 stale-state / Time-Filter-Entity 边界 / T02→T03 方案 2 adapter / T02→T04 边界 / 确定性策略 / Evidence 四列 / Integration edge-scoped / Gate A 决策 10 项。等待 Architecture Review（规划 PR）。
- 2026-08-14：**Gate A Architecture Review 修正已应用（planning/t02-intent-semantic-contract，等待复审）**：
  - **UNSUPPORTED ≠ None**：修复 stale-state 与 outcome taxonomy 冲突——四态 expected outcomes（COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED）都必须产生**完整 IntentResult**；固定原则："Expected semantic outcomes always produce an IntentResult." / "None means no valid T02 semantic result exists; it is not the representation of UNSUPPORTED."
  - **stale-state 重新冻结**：每次正常完成 interpretation（无论 outcome）都返回新完整 IntentResult 整体 overwrite 上一轮（上一轮 COMPLETE → 本轮 UNSUPPORTED 整体替换）；None 仅限无合法 semantic result 的 failure path——具体 path 与 Node 是否写 None 留 Gate B failure-boundary Review，不把 infrastructure / model failure 混进 expected outcome
  - **COMPLETE / PARTIAL 基于 required semantics**：COMPLETE = 当前 query intent 所需 semantic requirements 均已充分表达（不要求所有可选类别有值）；PARTIAL = 至少一个 required requirement 未解析；固定原则："Optional semantic field absence is not automatically partial interpretation."
  - **applicability / unresolved 边界**：IntentResult 必须能区分 not applicable vs required but unresolved（否则 PARTIAL 不可靠）；Gate A 只冻结语义能力，不强行设计所有 Optional 字段
  - **T02→T03 三层接口**：IntentResult → source-agnostic retrieval requirements → integration / source-specific adapter → T03 RetrievalCriteria；固定原则升级："Semantic interpretation ≠ retrieval requirement ≠ source-specific retrieval criteria."；RetrievalCriteria 保持 fixture / source-specific；fake source key vocabulary 不得进入 IntentResult；不强制创建 RetrievalRequirement DTO，Gate B 决定形态但不得删除逻辑层
  - **ambiguity 暴露不消歧**：删除"T02 ambiguity 不提前进入 T03"绝对表述——T02 必须显式暴露 interpretation ambiguity，不得静默选择；后续 application policy 可选 clarification / human input / domain rule / T03 facts 验证消歧；固定原则："T02 exposes ambiguity; it does not unilaterally resolve it."
  - **model failure 收窄**：不统一写 transient——transport / provider / auth / config / malformed typed output / model refusal 均属 model invocation / output-contract failure，**不属于 semantic outcome taxonomy**；failure classification / retryability / retry policy 留后续 failure / retry contract
  - **consumed-contract violation 边界**：normalized_question=None 可作为 Node / parser violation 代表，但 pure parser 可接收 `str`，Node adapter 保证输入契约（不强制所有内部函数 Optional[str] 检查）
  - **Integration edge 细化**：T02→T03 拆为两条逻辑 edge（T02 result → retrieval requirements；retrieval requirements → T03 RetrievalCriteria），不用一句 T02→T03 closed 掩盖 adapter contract
  - Gate A 决策表重写为 10 项最终结论（含 expected outcomes 全返 IntentResult / required-based 判定 / 三层接口 / model failure 边界）
  - 等待复审；Status 仍 in_progress；不得进入 Gate B。
- 2026-08-14：**Gate A 最终 Architecture Review 修正已应用（planning/t02-intent-semantic-contract，等待最终复审）**：
  - **固定主线术语修正**："结构化语义事实" → "**结构化语义解释与意图**"（消除与 Model-derived interpretation ≠ Authoritative business fact 的术语冲突）；固定原则："Semantic interpretation is structured inference, not authoritative fact."；术语约定：T02 产出不得称为 fact / semantic fact / structured fact（除否定 / 对比上下文），"fact" 表述只属 T03 authoritative facts
  - **Outcome → Retrieval Requirement Eligibility 冻结**：COMPLETE 可表达所需 requirements；PARTIAL 可表达已识别 needs + 补齐 unresolved 所需 facts（不假装 complete）；AMBIGUOUS 可表达 candidate-scoped / disambiguation-oriented requirements（例："需要验证哪些候选是正式企业指标"）；**UNSUPPORTED 默认不产生普通 downstream retrieval requirements**（未来需要单独设计，不在 Gate B 自动生成）；"retrieval requirements exists" ≠ "routing to T03 verified"
  - **Retrieval Requirement ≠ Routing**：固定原则 "Retrieval requirement is data, not routing." / "Having retrieval requirements does not authorize T02 to invoke T03."——T02 只产生 IntentResult / retrieval requirement data，不调用 / route / retry T03、不 clarification routing、不 terminate graph（属 application control flow / Node / Edge / Command / Runtime）
  - **AMBIGUOUS 后续边界**：可产生 candidate-scoped requirements 但不自动进 T03；policy 四选项（clarification / human input / domain rule / T03-assisted disambiguation）；ambiguous outcome ≠ routing decision
  - **UNSUPPORTED 边界补全**：expected outcome + 完整 IntentResult；UNSUPPORTED → RetrievalCriteria 不作为默认 adapter 行为；≠ None ≠ Runtime exception ≠ T03 NOT_FOUND
  - **resolved / candidate / unresolved / not-applicable 四语义状态**：IntentResult 必须可区分（否则四态 outcome 不可靠）；语义类别统一表述为 semantic interpretations（resolved or candidate），不暗示"所有已解析语义永远只是 candidates"；字段名 Gate B
  - **Integration edge 再细化**：T01→IntentResult / IntentResult→retrieval requirements / requirements→RetrievalCriteria / RetrievalCriteria→T03 RetrievalResult / RetrievalResult→T04 / compiled graph / real source——**data edge ≠ routing edge**
  - Gate A 决策表重写为 10 项最终结论（第 1 项 = interpretation not fact；第 6 项 = eligibility；第 7 项 = requirement data not routing；第 9 项 = lifecycle / routing authority 都不拥有；第 10 项 = edge-scoped + data edge ≠ routing edge）
  - Review Focus 更新为 10 项最终清单
  - 等待最终复审；Status 仍 in_progress；不得进入 Gate B。
- 2026-08-14：**Gate A 最终 Architecture Review：APPROVED（final consistency cleanup 完成，等待最终 Merge 确认）**：
  - **retrieval criteria 旧口径清理**（第三节）："T02 产生 retrieval criteria / semantic requirements" → "T02 产生 structured semantic interpretation 以及 source-agnostic retrieval requirements；source-specific RetrievalCriteria 由 integration / source-specific adapter 产生"——**T02 不直接产生 RetrievalCriteria**
  - **resolved / candidate 术语清理**（第三、四节）："T02 输出的一切 interpretation 都带语义候选性质" → "T02 输出始终属于 structured inference，不是 authoritative fact；其中既可以包含 resolved interpretation，也可以包含 ambiguous candidates"——保持 **resolved ≠ authoritative fact**，不再写 resolved = candidate；LLM 角色节同步（模型输出属 interpretation，可含 resolved / ambiguous candidates）
  - **RetrievalCriteria final boundary**（第五节）：删除"T02 可以生成它或映射到它"与"是否同一 contract 由 Gate A 决策"——RetrievalCriteria 是 T03 当前的 source-specific fixture，不是 T02 final semantic contract；具体 source lookup representation 由 integration / source-specific adapter 根据 source-agnostic retrieval requirements 映射得到
  - **adapter 三层表述**（第十三节）：方案 2 描述统一为 IntentResult → source-agnostic retrieval requirements → integration / source-specific adapter → RetrievalCriteria，不把 adapter 写成直接映射 fake source key；Evidence Planning 同步三层链路
  - **residual scan 无残留**：TASK-0034 / current.md / PR #64 不再出现"T02 产生 retrieval criteria""T02 直接生成 RetrievalCriteria""一切 interpretation 都是 candidate""IntentResult → RetrievalCriteria 直接 adapter""是否同一 contract 待 Gate A 决策"
  - Status 仍 **in_progress**；Gate A = Architecture Review **APPROVED**；final consistency cleanup **completed / pending merge**；**不得进入 Gate B**。
