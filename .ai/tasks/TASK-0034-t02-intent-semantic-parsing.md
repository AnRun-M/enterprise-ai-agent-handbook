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

> **"T02 将 T01 产生的 normalized_question 解释为后续 Runtime 可以显式消费的结构化语义事实；它负责 semantic interpretation，但不负责生成 SQL、不读取权威 metadata、不做权限风险裁决，也不把模型推断结果伪装成外部事实。"**

输入：`normalized_question`（T01 产物）。输出：semantic / intent contract（**IntentResult**）。下游：T03 retrieval criteria、T04 SQL generation、可能的 clarification / failure control flow。本轮只冻结 contract。

## 二、T01 / T02 边界

| | T01（representation normalization） | T02（semantic interpretation） |
|---|---|---|
| 职责 | trim / whitespace canonicalization / empty detection | 识别 metric / dimensions / entities / time range / filters / aggregation intent / query intent |
| 产物 | normalized_question | IntentResult（semantic / intent contract） |

固定原则：

> **"Normalization changes representation; semantic parsing interprets meaning."**

**不得把 T01 职责重新搬进 T02**：T02 假定输入已是 normalized 形式（空输入由 T01 在 lifecycle 层处理）；T02 不做 whitespace canonicalization、不重复 empty detection。

## 三、T02 / T03 边界（Gate A 重点）

- **T02 产生**：retrieval criteria / semantic requirements（"用户想查 GMV"）
- **T03 产生**：authoritative facts（"GMV = paid_amount − refund"——来自 External Source of Truth）

固定原则：

> **"Semantic interpretation may identify what facts are needed; it must not manufacture authoritative facts."**

（语义解释可以识别需要哪些事实；不得制造权威事实。）

T02 可以推断用户想要哪个 metric / dimension / entity 的**语义候选**；但 metric 定义、region mapping、业务口径、canonical rule **必须来自 T03 权威源**。T02 输出的一切 interpretation 都带语义候选性质，不是已核验事实。

## 四、LLM 的角色

T02 是未来 Model Decision 挂载点，但必须区分：

| | Model-derived interpretation | Authoritative business fact |
|---|---|---|
| 可输出 | metric candidate / dimension candidate / time expression interpretation / intent classification | ✗ 禁止 |
| 不可成为 | — | schema source / metric definition source / permission source / business-rule authority |

**不得因为使用 LLM 就把结果称为"事实"**。模型输出是 candidate interpretation，只有经 T03 权威检索确认的内容才具有事实地位。Gate A 冻结：T02 的 output contract 必须显式表达"候选 / interpretation"性质，不得以 facts 自居。

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

**不要因为 T03 当前有 RetrievalCriteria 就直接把它升级成 T02 最终 schema**。RetrievalCriteria 仍是 fixture；T02 可以生成它或映射到它，但两者是否同一 contract 由 Gate A 决策（见第十四节：**不是同一 contract**）。

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

边界例：interpretation 无歧义（"查询 GMV"）但 source 有多候选 → 这是 **T03 AMBIGUOUS**；interpretation 本身有歧义（"销售额"）→ **T02 层先暴露**，不提前进 T03 检索。T02 不得把 interpretation ambiguity 映射为 T03 的 NOT_FOUND / UNAVAILABLE，也不得静默取第一个候选。

## 八、Failure / Outcome Contract

**不机械复制 T03 五态**——T02 是 semantic interpretation，T03 是 authoritative retrieval，Outcome taxonomy 可以不同。

| 情况 | 类别 | 表达 |
|---|---|---|
| complete interpretation（全部语义类别解析） | **expected application outcome** | COMPLETE |
| partial interpretation（部分类别可解析，如 metric 已定、time expression 不明） | **expected application outcome** | PARTIAL |
| ambiguous interpretation | **expected application outcome**（语义层） | AMBIGUOUS |
| unsupported request（无法映射任何语义类别 / 域外，如"帮我删除数据"） | **expected application outcome**（→ clarification control flow） | UNSUPPORTED |
| invalid semantic input（normalized_question 为 None / 契约外输入） | **consumed-contract violation** | ValueError（不进入 outcome taxonomy） |
| model failure（LLM 调用失败 / malformed output 无法按 typed contract 解析） | **model failure**（infrastructure / transient） | 不属 outcome；应用 failure boundary 处理；retry 属 Part 05 |
| runtime exception | **programming error** | 异常传播 |

**冻结：T02 outcome taxonomy = COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED 四态**（教学规模）。**不要全塞 failure_reason**——四类 expected outcome 各自表达语义，只有 consumed-contract violation 抛 ValueError。

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

- success：返回**完整**新 IntentResult（整体替换）
- failure / unsupported：显式写 `intent_result: None`（失效 stale derived，同 T01 failure 显式 `normalized_question: None` 模式——**failure 显式 invalidates derived intent，防止旧派生值在 State merge 后残留**）

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
| 方案 2（推荐） | T02 产 **IntentResult**；另有 **deterministic adapter：IntentResult → RetrievalCriteria**（由 metric / dimension / entity / filter intent tokens 推导检索 keys） | ✅ semantic interpretation ≠ retrieval query representation；T02 不被 fixture 反向绑定；adapter 可独立单测 |

**Gate A 决策：方案 2。** 固定原则：**"Semantic interpretation ≠ retrieval query representation."**（语义解释不等于检索查询表示——IntentResult 承载用户语义意图，RetrievalCriteria 承载对权威源的检索查询，两者由确定性 adapter 连接。）RetrievalCriteria **保持 fixture 身份不变**（T03 侧不修改）；具体 adapter 实现属 Gate B/C。

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
| **需要新增** | T02 unit evidence（deterministic fake parser）；semantic ambiguity（interpretation vs authoritative-source）；stale-state invalidation（整体 overwrite + failure None）；IntentResult → RetrievalCriteria adapter；T01 → T02 integration |
| **尚不能验证** | 真实 LLM interpretation quality；production multilingual semantic parsing；真实 business ontology；T03 → T04；full compiled graph；e2e |

## 十七、Integration Closure 设计（edge-scoped）

T02 进 main 后，**不要笼统宣布 T01 / T03 Integration closed**。按 capability edge 记录：

```
T01 → T02   （edge-scoped：deferred / closed）
T02 → T03   （edge-scoped：deferred / closed）
T03 → T04   （edge-scoped：deferred / closed）
compiled graph（edge-scoped：deferred / closed）
real source （edge-scoped：deferred / closed）
```

固定表述（加入本文件与 current.md planning）：

> **"Integration evidence is edge-scoped, not task-wide."**

（Integration 证据按 capability edge 记录，不是 task 级整体声明。）

## 十八、Gate A 最终决策（10 项，不得留"Implementation 时再看"）

| # | 决策 | 结论 |
|---|---|---|
| 1 | T02 最终 semantic contract 形态 | **typed semantic contract（方案 C）**：IntentResult，语义类别 = metric candidates / dimensions / entities / time range（semantic time expression）/ filters / aggregation intent / query intent；字段结构 Gate B 落地，语义边界冻结 |
| 2 | 是否独立 IntentResult | **是**——T02-owned derived state，单个对象 |
| 3 | IntentResult 与 RetrievalCriteria 关系 | **方案 2**：IntentResult + deterministic adapter（IntentResult → RetrievalCriteria）；RetrievalCriteria 保持 T03 fixture 身份；"Semantic interpretation ≠ retrieval query representation." |
| 4 | semantic ambiguity contract | **双层**：interpretation ambiguity（T02，AMBIGUOUS 四态之一 + 对象内候选）+ authoritative-source ambiguity（T03 五态 AMBIGUOUS）；不混成一个字段 |
| 5 | stale semantic state invalidation | **整体对象 overwrite**（单 channel 天然失效全部旧子值，无需逐字段 contract）；failure / unsupported 显式写 `None`（同 T01 failure None 模式） |
| 6 | time semantics 边界 | T02 只输出 **semantic time expression token**；timezone / business / fiscal calendar / data freshness cutoff = 外部事实，T02 不静默猜 |
| 7 | authoritative fact boundary | T02 只 identify needed facts（candidate），**不 manufacture facts**（metric 定义 / region mapping / VIP rule / paid-status canonical rule 需 T03）；"Semantic interpretation may identify what facts are needed; it must not manufacture authoritative facts." |
| 8 | T04 consumption boundary | T04 未来消费 **semantic intent（IntentResult）+ T03 trusted facts**；T02 contract 不只服务 T03；T04 仅接口位置 |
| 9 | shared lifecycle authority | T02 Node **默认不写 status / failure_reason**（Outcome ≠ Agent lifecycle，同 T03 连续，不复制 T01 RUNNING→FAILED）；若未来需要生命周期转换，必须单独 transition-authority Review |
| 10 | Integration evidence edge-scoped 模型 | **"Integration evidence is edge-scoped, not task-wide."**——T01→T02 / T02→T03 / T03→T04 / compiled graph / real source 各自 deferred / closed |

## 十九、禁止事项（本轮）

- T02 implementation（examples / tests）
- 真实 LLM
- T04 implementation
- T06 / T07
- 修改 T01 / T03 / T05 implementation
- ROADMAP / content-map / Chapter 正文 / ADR / principles / architecture-map / Pattern Backlog（TASK-0031）

只允许：`TASK-0034`、`current.md`、规划 PR Description。

## 二十、验收标准（Gate A 阶段）

- [x] 固定主线逐字冻结（semantic interpretation / 不生成 SQL / 不读权威 metadata / 不做权限裁决 / 不伪装事实）
- [x] T01 / T02 边界（representation vs interpretation；"Normalization changes representation; semantic parsing interprets meaning."）
- [x] T02 / T03 边界（semantic requirements vs authoritative facts；"must not manufacture authoritative facts"）
- [x] LLM 角色（Model-derived interpretation ≠ Authoritative business fact；candidate 性质显式）
- [x] Contract 方案比较（A / B / C × 11 维度）→ 方案 C 决策
- [x] Ambiguity 双层（interpretation vs authoritative-source，不混字段）
- [x] Outcome taxonomy（四态 expected outcomes / consumed-contract violation / model failure / runtime exception 分类明确；不机械复制 T03 五态）
- [x] Ownership（IntentResult = T02-owned derived；Field write capability ≠ ownership）
- [x] Stale semantic state（整体 overwrite + failure None，Gate A 预先回答）
- [x] Time / Filter / Entity 边界（semantic token vs external facts；推荐链路）
- [x] T02 → T03 接口（方案 2 adapter；RetrievalCriteria 保持 fixture）
- [x] T02 → T04 边界（IntentResult 不只服务 T03）
- [x] 确定性策略（fake parser 优先；typed contract + bounded taxonomy；第一版不接真实 LLM）
- [x] Evidence Planning 四列制（已有 / 需新增 / 尚不能验证）
- [x] Integration Closure edge-scoped（"Integration evidence is edge-scoped, not task-wide."）
- [x] Gate A 决策 10 项全部给出明确结论
- [ ] 等待 Architecture Review（Gate A Review PR）

## 完成记录

- 2026-08-13：任务创建（in_progress，planning/t02-intent-semantic-contract 分支）。Gate A 草案完成：固定主线 / T01-T02 / T02-T03 边界 / LLM 角色 / Contract 方案比较（A/B/C × 11 维度）→ 方案 C / Ambiguity 双层 / Outcome taxonomy 四态 / Ownership 与 stale-state / Time-Filter-Entity 边界 / T02→T03 方案 2 adapter / T02→T04 边界 / 确定性策略 / Evidence 四列 / Integration edge-scoped / Gate A 决策 10 项。等待 Architecture Review（规划 PR）。
