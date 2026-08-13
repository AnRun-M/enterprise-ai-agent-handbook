# TASK-0033：T03 元数据与业务规则检索（Gate A：Architecture / Contract）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-11 |
| Updated | 2026-08-13 |
| Related ADR | ADR-0002 / ADR-0005（规则分层） |
| Related Task | TASK-0029（T03 = Wave 1）、TASK-0032（T01 Gate A，同分支规划） |
| Related Example | examples/text2sql_state（默认载体） |
| Related Principle | architecture-map（External Source of Truth / Model Context / 引用策略） |

## 定位

Wave 1 并行任务之一（T01 / T03 均无 Strong dependency）。**Gate A：Architecture / Contract 已冻结并通过 Review（PR #59 合并）；Gate B Implementation + Gate C Tests 已完成（feature/t03-metadata-retrieval，本分支，最终复审 APPROVED）；Gate D Documentation 已完成（第 20 章，draft）；Task Merge Gate Architecture Review 已通过（方案 A fact-level binding → identity/evidence 分离 → 最终 code-contract cleanup 已应用，等待 Merge 确认）；Gate E 待后续。**

---

## 一、仓库事实核对（2026-08-11）

- **canonical T03**：元数据与业务规则检索——表 / 字段 / 业务口径 / 权限元数据（责任方：确定性检索 RAG）
- **canonical 顺序**：T01 → T02（意图解析）→ T03（检索）→ T04（生成）——**Runtime Pipeline 关系；Implementation dependency ≠ Runtime dependency**（TASK-0029 冻结）
- **architecture-map**：External Source of Truth（语义层 / 权限 / 元数据 / 数据库——判定问题 5：来自外部事实源的信息**不要无条件复制进 State**）；引用策略（ID / URI / version / digest / summary）；Model Context 第三层（State 切片 + 检索内容组装）
- **text2sql_state 现状**：无 T03 代码（README 待实现）
- **TASK-0029**：T03 Owns SemanticContext（Proposed）；Weak：T02（指标选择语义）

## 二、职责边界（冻结）

**概念区分（只引用，不重新定义）**：

| 概念 | 定义（引用） |
|---|---|
| **Metadata** | 表 / 字段的结构性信息（external source） |
| **Business Rule** | 业务口径 / 规则（external source；ADR-005 规则分层） |
| **Semantic Context** | 检索后组装、供 SQL 生成使用的上下文（T03 产出） |
| **External Source of Truth** | 语义层 / 权限 / 元数据 / 数据库——事实的权威来源（architecture-map） |
| **Model Context** | 一次模型调用可见的组装输入（ch03）——检索结果经 Context 组装进入模型 |
| **Memory** | 跨执行边界信息（ch07）——T03 ≠ Memory |

**T03 只负责**："根据显式检索条件，取得后续 SQL generation 所需的**可信上下文**（Metadata + Business Rule 的检索与结构化）"。

**T03 不负责**：Intent Classification（T02）/ SQL Generation（T04）/ Validation（T05）/ Risk-Permission（T06）/ Repair（T07）——权限与风险检查是 T06，T03 只提供权限元数据（不裁决）。

## 三、T02 / T03 边界（Proposed consumed contract）

- Runtime Pipeline：T01 → T02 → T03 → T04；**但 Implementation 可独立**（T03 Gate A 独立完成）
- **未来 consumed input**（来自 T02 的指标 / 维度 / entity / time range / filters / intent facts）——**当前 T02 尚未实现**
- **只能冻结 Consumer Contract**：T03 消费"检索条件"（Proposed consumed contract / fixture contract）——**不得提前定义 T02 完整字段结构**；不假装 T02 schema 已存在

## 四、Retrieval Result：Reference 与 Materialized Context 双层（Review 修正）

统一 `RetrievalContext` 容易混淆"可持久化引用"与"T04 真正消费的事实内容"——**拆成两层语义**：

### A. Retrieval Reference / Provenance（适合持久化 / 进入 State）

- source reference / identifier
- kind
- freshness / version evidence
- optional digest / optional rule id

**用途**：Trace / Replay / Provenance / Reconstruction。

### B. Materialized Retrieval Payload（当前请求实际取得的事实内容）

- schema facts
- metadata
- business-rule content

**用途**：Context Builder → Model Context → T04 generation。**不要求完整 payload 长期复制进 State**（architecture-map 引用策略）。

**固定核心表述：**

> **External Source of Truth 的事实不无条件复制进 State；T03 同时建立可追踪的 retrieval references / provenance，并向当前调用提供 materialized retrieval payload；Model Context 在调用边界按需组装。**

**`RetrievalContext` 定位（Review 修正）**：保留名称作为 **Proposed umbrella contract**——**不等于"所有 retrieved content 全部长期存入 Graph State"**。最终实现可采用：

```
RetrievalResult
├── outcome
├── references
└── materialized payload / request-scoped view
```

**Gate A / Gate B 边界（Review 修正）**：Gate A 已冻结**语义 contract**——outcome + references/provenance + materialized payload 三层职责。**具体 Python 类型、字段名与内部表示在 Gate B Implementation 中落地，但不得改变 Gate A 已冻结的语义边界；若实现需要改变这些边界，必须返回 Architecture Review，不得在 Gate B 自行重定义 contract。** TASK-0029 只要求 ownership，**不让 planning 变成 schema spec**。

## 五、Source of Truth 与 Provenance（冻结，Review 修正最小语义）

- **Source of Truth**：**Retriever 不创造业务事实**——只从 schema metadata / metric definitions / business rules / catalog / 外部权威源取得事实；**LLM 不得成为事实源**（ADR-005 规则分层：业务规则不靠模型记忆）
- **Provenance 最小语义（Review 修正）**：**必须能够识别——事实来自哪个 source，以及使用的是哪个可区分版本 / 快照 / 时点**。推荐抽象：

```
source_ref
+
freshness / version evidence
```

后者可能表现为：**version / revision / timestamp / etag / digest / snapshot id**——**具体字段依 source capability 决定，不强迫所有 Source 都存在名为 version 的字段**。生产治理细节（完整审计）留 Part 05。

## 六、Retrieval Outcome（Review 分层）

**检索失败如何被 Runtime 看见**（不靠空串 / None 混用 / 隐式 fallback 掩盖）——建立分层 Outcome：

| Outcome | 含义 |
|---|---|
| **complete** | 所需事实完整 |
| **partial** | 部分事实可用——**是否继续由消费方 / 应用策略决定** |
| **not_found** | 权威源无匹配事实——**不等同 infrastructure exception** |
| **ambiguous** | 存在多个合法映射——需上层澄清 / 处理 |
| **unavailable** | 权威源当前不可访问——**operational failure** |

**T03 负责报告 Outcome，不越权决定所有后续业务路由**；**不实现 retry**（Part 05）。

## 七、T03 → T04 内容桥接（Review 新增）

**必须回答"T04 实际拿什么生成 SQL？"**——Gate A 最终表述：

```
retrieval criteria
→ Retriever
→ outcome + provenance/references + materialized facts
→ Context Builder
→ Model Context
→ T04
```

**不给 T04 只有 URI / digest**（否则没有生成 SQL 所需事实）——T04 实际消费 **materialized payload（经 Context Builder 组装）**；references / provenance 用于 Trace / Replay / 可解释性。

## 八、Memory 边界（冻结）

- **T03 retrieval ≠ Memory**：Memory（ch07，跨执行）可以影响未来检索（如常用指标偏好），但 **authoritative metadata / business rule 仍来自 External Source of Truth**——**不得把旧对话缓存直接当业务事实**

## 九、Evidence（四列制）

- **代码事实**：text2sql_state 无 T03 代码；仓库无 catalog / retriever
- **测试事实**：无 T03 测试（尚不存在）
- **设计建议**：RetrievalContext（Proposed）/ 引用策略 / provenance 最小集 / failure 语义（本文件）
- **尚未验证**：retriever 行为；与 T02 真实串联（Integration deferred——T02 未实现）；与 T04 生成的真实消费

## 十、Architecture Decisions（Gate A 最终收敛）

| # | Decision | 结果 |
|---|---|---|
| 1 | 单一大 RetrievalContext | **不冻结为大 DTO**（Proposed umbrella contract；Python 类型与字段在 Gate B 落地，不得改变 Gate A 语义边界） |
| 2 | reference / provenance 与 materialized payload | **语义拆分**（双层：可持久化引用 vs 请求实际消费事实） |
| 3 | outcome model | **complete / partial / not_found / ambiguous / unavailable** |
| 4 | provenance | **source + freshness / version evidence**（version / revision / timestamp / etag / digest / snapshot id 依 source capability） |
| 5 | State 持久化 | **只持久化必要引用 / 控制事实；完整事实不无条件复制进 State** |
| 6 | T04 实际内容 | **通过 request-scoped materialization + Context Builder 获取**（不只给 URI / digest） |

## 十一、Review Gate（统一）

- Gate A Architecture / Contract：**completed** ✅（PR #59 Architecture Review 通过并合并）
- Gate B Implementation（text2sql_state retriever + 测试）：**completed** ✅（三轮 Review 修正后最终复审 APPROVED）
- Gate C Tests / Evidence：**completed** ✅（pytest / ruff / mkdocs --strict 通过）
- Gate D Documentation（第 20 章 T03）：**completed** ✅（`docs/04-text2sql/ch20-metadata-business-rule-retrieval.md`，draft；T04 / Context Builder 仅接口位置）
- **等待 Task Merge Gate 最终 Review** → Task Merge → Gate E（等 T02/T04 进 main，deferred → closed）。

## 验收标准（Gate A 阶段）

- [x] 职责边界冻结（Metadata / Business Rule / Semantic Context / External Source of Truth / Model Context / Memory 区分；T03 只负责可信上下文检索）
- [x] T02 / T03 边界（Proposed consumed contract；不假装 T02 schema 已存在）
- [x] Reference / Materialized Payload 双层（Review 修正）
- [x] RetrievalContext 定位（Proposed umbrella contract，不冻结大 DTO）
- [x] Source of Truth（Retriever 不创造事实；LLM 不得成为事实源）
- [x] Provenance 最小语义（source + freshness / version evidence，依 source capability）
- [x] Retrieval Outcome 分层（complete / partial / not_found / ambiguous / unavailable）
- [x] T03 → T04 内容桥接（materialized facts 经 Context Builder 进 Model Context，不只给 URI/digest）
- [x] Memory 边界（T03 ≠ Memory；authoritative 来自 External Source of Truth）
- [x] Evidence 四列制；未实现 Retriever
- [x] Architecture Decisions 6 项收敛
- [ ] 等待 Architecture Review 复审

## 完成记录

- 2026-08-11：任务创建（in_progress）；Gate A 完成；等待 Architecture Review（planning/wave1-t01-t03-contracts 分支，与 T01 同分支规划）。
- 2026-08-11：**PR #59 Architecture Review 修正**（commit：docs: refine wave1 input and retrieval contracts）：Retrieval 拆 **Reference / Provenance 与 Materialized Payload 双层**（引用可持久化进 State，事实内容请求级物化）；RetrievalContext 收窄为 **Proposed umbrella contract**（不冻结大 DTO；**Gate A 冻结语义 contract，Python 类型 / 字段名 / 内部表示在 Gate B 落地，不得改变已冻结语义边界；若需改变则返回 Architecture Review**）；**Retrieval Outcome 分层**（complete / partial / not_found / ambiguous / unavailable；partial 是否继续由消费方决定；unavailable 为 operational failure）；**Provenance 最小语义修正**（source + freshness / version evidence——version / revision / timestamp / etag / digest / snapshot id 依 source capability，不强迫所有 Source 有 version 字段）；**T03 → T04 内容桥接**（materialized facts 经 Context Builder 进 Model Context，不只给 URI/digest）；Architecture Decisions 6 项收敛。
- 2026-08-11：**PR #59 合并（commit eb9d324）→ Gate A 正式通过**（与 T01 同 PR）。
- 2026-08-11：**Gate B Implementation + Gate C Tests 完成（feature/t03-metadata-retrieval）**：
  - contract 类型：`retrieval_types.py`——`RetrievalOutcome`（五态 Enum，强类型）/ `RetrievalReference`（frozen，source_ref + evidence）/ `MaterializedFacts`（frozen，schema_facts + business_rules；**教学规模实现选择**）/ `RetrievalResult`（frozen：outcome + references + materialized；无路由意图）/ `RetrievalCriteria`（**Proposed consumed contract / fixture**，非 T02 最终 schema）
  - fake authoritative source：`metadata_source.py`——`InMemoryMetadataSource`（确定性 in-memory，不可变，可表达 exists / missing / ambiguous / unavailable；partial 由 Retriever 聚合）+ `build_fixture_source()`（catalog-v1：orders / gmv / 华东 / ambiguous_metric / broken_source）
  - retriever：`retrieval.py`——`MetadataRetriever`（DI 注入 source；读取事实不创造事实；outcome 聚合唯一顺序：UNAVAILABLE > AMBIGUOUS > NOT_FOUND > PARTIAL > COMPLETE；空 criteria = COMPLETE 边界决定；references + materialized 分离）
  - node adapter：`retrieval_node.py`——`retrieve_metadata_node(state, retriever, criteria)` 只写 `retrieval_result`；**不触碰 shared lifecycle（status / failure_reason）——Retrieval Outcome ≠ Agent lifecycle，不复制 T01 的 RUNNING→FAILED 规则**（本轮 Review Focus）
  - State：`Text2SQLState` 增加 `retrieval_result: RetrievalResult | None`（教学规模小型 payload 进 State，明确标注非生产建议；不保存 source object / repository client / connection）
  - `__init__.py` 按惯例导出 T03 API
  - 测试：`tests/text2sql_state/test_retrieval.py`（五态 / provenance / multiple refs / materialized 与 refs 分离 / determinism / source 不被修改 / 无全局可变状态 / 无静默兜底 / 无 LLM 事实 / 无路由意图 / fixture 标识）+ `test_retrieval_node.py`（partial update / lifecycle 边界 / 不修改输入 State / 无跨调用污染）
  - Evidence：**Contract-level verified**；Integration = **deferred**（T02 未实现 / T04 未集成 / 真实 External Source 未接入）
  - 等待 Gate B/C Architecture + Implementation Review；Status 仍 in_progress。
- 2026-08-12：**Gate B/C Review 修正已应用（feature/t03-metadata-retrieval，等待最终复审）**：
  - **order-dependency 修复**：取消 UNAVAILABLE early return——完整扫描所有 criteria keys，扫描完成后统一计算 outcome。固定原则：**"Outcome priority ≠ iteration short-circuit."** + **"除非 contract 明确声明顺序有业务语义，retrieval criteria 的排列顺序不应改变逻辑检索结果"**
  - **UNAVAILABLE payload policy（策略 A）**：整体 outcome = UNAVAILABLE 时仍保留其它可成功读取 key 的 references / materialized facts（与 PARTIAL"保留找到事实"理念连续）；与 criteria 顺序无关
  - **empty criteria = consumed-contract violation**：`raise ValueError("retrieval criteria must contain at least one key")`——撤销"empty = COMPLETE"（Gate B 新增业务决策，非 Gate A 冻结）；NOT_FOUND ≠ 无 criteria、UNAVAILABLE ≠ invalid criteria；不新增第六个 RetrievalOutcome；未来 T02 若需"合法零事实请求"必须返回 Architecture Review 显式设计
  - **strict CatalogEntry kind**：`CatalogEntryKind` Enum（SCHEMA / BUSINESS_RULE），`CatalogEntry.kind` 强类型，Retriever 用 Enum 比较 + 防御性 fail-fast——未知 kind 不得静默忽略。原则：**"Retrieval Outcome describes authoritative lookup semantics; malformed source data is a contract error."**（不为其新增 RetrievalOutcome）——**最终复审修正：kind 标注升级为 CatalogEntry 构造级运行时校验（`__post_init__` 拒绝非 CatalogEntryKind，TypeError fail-fast）——"Static type annotation ≠ runtime contract validation."；malformed source data 在 source boundary 失败，不进入 Retrieval Outcome 语义**（见下一条记录）
  - **permutation-invariance evidence**：新增（orders, gmv）↔（gmv, orders）完全相等；（orders, broken_source）↔（broken_source, orders）完全相等；（orders, ambiguous_metric, broken_source）全部 6 排列 outcome 恒 UNAVAILABLE 且结果一致——输出经 `sorted(set(keys))` canonical 化（去重 + 排序），等价 criteria set → 等价 RetrievalResult
  - **duplicate keys 去重**：criteria 视为逻辑 key set——（orders, orders）不产生重复 facts / references
  - evidence 三类区分：repeated deterministic / permutation-invariance / source-contract strictness
  - lifecycle 边界保持：Node 只写 retrieval_result，不写 status / failure_reason / next_action / route；State 边界保持（教学规模选择）
  - **清理旧事实**：empty = COMPLETE / unavailable early return 是最终 contract / deterministic 仅等同 same tuple / CatalogEntry.kind 可任意 str / unknown kind 可静默忽略
  - Gate B/C 状态：**修正中，等待最终复审**；Status 仍 in_progress；不得进入 Gate D。
- 2026-08-12：**Gate B/C 最终复审修正已应用（CatalogEntry runtime contract，等待最终确认）**：
  - **CatalogEntry runtime strictness**：`kind: CatalogEntryKind` 仅是静态类型标注——dataclass 不会自动在 runtime 校验类型；新增 `__post_init__` 运行时校验（`not isinstance(self.kind, CatalogEntryKind)` → `raise TypeError("CatalogEntry.kind must be a CatalogEntryKind")`）——malformed source entry 在进入 Retriever 前 fail fast
  - **固定原则（新增）**：**"Static type annotation ≠ runtime contract validation."**（静态类型标注不等于运行时契约校验）；**"Malformed authoritative-source data should fail at the source boundary before retrieval semantics are evaluated."**（畸形权威源数据应在 source boundary 失败，而不是进入 Retrieval Outcome 语义）
  - **source-contract test**：`test_catalog_entry_rejects_non_enum_kind_at_construction`——`CatalogEntry(key="x", kind="unknown_typo", ...)`（`# type: ignore[arg-type]`）断言 TypeError；原 `CatalogEntryKind("unknown_typo")` → ValueError 测试保留但明确为 **Enum representation test**（不是 CatalogEntry runtime contract 的唯一证据）
  - **Validation 分层（文档明确）**：① CatalogEntry construction = source contract validation（主要校验路径）② Retriever = 消费已验证的 CatalogEntry ③ Retriever else = defensive impossible-branch protection（不把 malformed data 拖到 materialization 中途作为主要校验路径）
  - **同步**：把"unknown kind Enum 构造失败"口径收窄为"**CatalogEntry source boundary 运行时拒绝非 CatalogEntryKind；Enum 本身也拒绝未知值**"
  - 其它 contract 全部保持：sorted(set(keys)) / permutation invariance / duplicate dedup / empty = ValueError / UNAVAILABLE full scan + payload policy A / outcome priority / 五态 / Node lifecycle 边界 / State 边界 / Integration deferred
  - Gate B/C 状态：**修正中，等待最终确认**；Status 仍 in_progress；不得进入 Gate D。
- 2026-08-12：**Gate B/C 最终复审修正已应用（source identity contract，等待最终确认）**：
  - **source index / entry identity validation**：`InMemoryMetadataSource.__init__` 构造阶段校验每个 index_key 下的 `CatalogEntry.key == index_key`，mismatch 即 `raise ValueError("CatalogEntry.key must match source index key: ...")`——防止 silent provenance corruption（lookup("orders") 却产出 `source_ref=catalog:customers`）；构造时失败，不进入 lookup / Retriever / Retrieval Outcome
  - **固定原则（新增）**：**"Source index identity must agree with entry identity."** + **"Provenance correctness starts at source construction, not at retrieval output formatting."**（权威源索引键与事实条目标识必须一致；provenance 的正确性从 source construction 开始，而不是在 Retriever 输出时修补）
  - **不在 Retriever 掩盖 malformed source**：禁止用 criteria_key 拼 source_ref 掩盖 entry.key mismatch——Retriever 消费已通过 source contract validation 的 entries。Validation 分层更新为四层：① CatalogEntry construction = field runtime validation ② InMemoryMetadataSource construction = index / entry identity validation ③ MetadataRetriever = trusted source consumption ④ RetrievalReference = provenance output（+⑤ Retriever else = defensive impossible-branch protection）
  - **mismatch contract test**：`test_source_rejects_entry_key_mismatch`——key="customers" 的 entry 放入 index "orders" → ValueError（match 断言）
  - **provenance identity chain 正向证据**：criteria "orders" → source index "orders" → CatalogEntry.key "orders" → `source_ref=catalog-v1:orders` 完整 chain（仍为 fake source contract evidence，不宣称生产 catalog 已验证）
  - **收窄 immutable 表述**：InMemoryMetadataSource docstring"构造后不可变"→ **read-only source snapshot**（构造时复制调用方 entries，公开 API 仅只读 lookup，调用方后续修改原始容器不影响 source snapshot；不声称 Python 对象绝对 immutable）
  - **snapshot isolation test**：`test_source_snapshot_isolated_from_caller_container`——修改 caller_entries 后 source.lookup 结果不变（constructor copy / snapshot isolation 方向）
  - 其它 contract 全部保持：CatalogEntry.kind runtime validation / Enum strictness / full scan / outcome priority / UNAVAILABLE payload policy A / empty = violation / sorted(set(keys)) / permutation invariance / duplicate dedup / 五态 / Node lifecycle 边界 / State 边界 / Integration deferred
  - Gate B/C 状态：**修正中，等待最终确认**；Status 仍 in_progress；不得进入 Gate D。
- 2026-08-13：**Gate B/C 最终复审 APPROVED**。
- 2026-08-13：**Gate D Documentation 完成（feature/t03-metadata-retrieval）**：
  - 创建 `docs/04-text2sql/ch20-metadata-business-rule-retrieval.md`（状态：**draft**，T03 完整承载；T04 / Context Builder 仅接口位置）——按 TASK-0029 Candidate Mapping（Ch20 = T03）
  - 结构 20.1-20.12：为什么需要可信事实 / 职责与边界（六概念，T03 ≠ Memory）/ Retrieval Outcome 五态 + priority / 三层 Retrieval Contract / Criteria Set 语义 / Fake Authoritative Source / Source Contract 五层 + Provenance Identity Chain + snapshot 边界 / Node 与 Graph State / Evidence 与未验证（10 项）/ T02-T04 接口位置 / 常见误区 10 条 / 总结
  - 固定主线逐字保持；四列制证据；正文不写死 pytest 数量；不宣称 e2e / production integration verified
  - 4 张 Mermaid（pipeline / outcome≠lifecycle / source contract 链 / T02→T04 接口）
  - `docs/04-text2sql/index.md` 新增"检索与生成"分区；`mkdocs.yml` 新增第 20 章导航
  - content-map / ROADMAP 未修改（无 ch19-ch25 逐章行惯例，Part 4 聚合行保持"进行中"）；Chapter 20 标 draft 不标 completed
  - Evidence：**Contract-level verified**；Integration：**deferred**（T02 未实现 / T04 未集成 / 真实 External Source 未接入）
  - 等待 Task Merge Gate 最终 Review；Status 仍 in_progress。
- 2026-08-13：**Task Merge Gate Review 修正已应用（方案 A：fact-level provenance binding，等待最终确认）**：
  - **缺口**：references 与 materialized facts 是两个独立 tuple——多 facts / ambiguous candidates 时消费者无法判断"某条 fact 具体来自哪个 source_ref / evidence"（只有 aggregate / result-level provenance，但 Chapter 20 的"Reference tells us where the fact came from"易被理解为 fact-level lineage）
  - **采用方案 A（最小 fact-to-reference binding，二选一已决）**：`RetrievalReference` 增加 `fact_id`；新增 `MaterializedFact`（fact_id + content）；`MaterializedFacts.schema_facts / business_rules` 改为 `tuple[MaterializedFact, ...]`；同一条 entry 同时产出 reference 与 fact，共享 fact_id
  - **fact_id deterministic**：`f"{source_name}:{entry.key}:{entry.evidence}"`——纯字符串构造、不依赖 object identity / 随机 UUID、permutation-invariant、duplicate-dedup 后稳定（无 Architecture Conflict，无需随机 identifier）
  - **binding tests（6 项）**：每条 fact 唯一可解析 binding / schema 与 rule 绑定到正确 source / permutation 后 binding 不变 / ambiguous candidates 各自保留 provenance（revision-1 vs revision-2）/ duplicate criteria 不产生重复 binding / fact_id deterministic 且稳定
  - **Chapter 20 修正**：20.4 三层 contract 加 fact_id binding 机制与代码示意；20.7 provenance identity chain 加 fact_id 层；20.9 evidence 加 fact-to-reference binding verified（未验证补充 production lineage schema / per-fact audit lineage，不宣称 production lineage verified）；20.12 总结 pipeline 修正为 **T01 → T02 → T03 → T04**（原遗漏 T02）；20.2 permission metadata 表述修正（"T03 只提供权限元数据（不裁决）"→"当前 T03 不实现权限元数据检索，T06 属权限裁决；未来扩展需明确 authoritative-source contract，不在本章预设"）
  - 其它 contract 全部保持：五态 / priority / full scan / payload 策略 A / empty violation / criteria set / permutation / dedup / CatalogEntry runtime validation / source identity / snapshot / Node lifecycle / State 边界 / T02 fixture / Integration deferred
  - Evidence：**fact-to-reference provenance binding verified**（教学 Contract 级）；production lineage / production provenance schema 仍未验证
  - Gate 状态：**修正中，等待 Task Merge Gate 最终确认**；Status 仍 in_progress；不得进入 Gate D。
- 2026-08-13：**Task Merge Gate 最终复审修正已应用（identity / evidence 分离，等待最终确认）**：
  - **Contract 缺口修复**：原 fact_id = `f"{source}:{entry.key}:{entry.evidence}"` 存在 collision 风险——source contract 只保证 `entry.key == index_key`，不保证同 key 下 evidence 唯一；合法 source 可能出现同 key 同 evidence 不同 content → 不同事实相同 fact_id（fixture 的 revision-1 / revision-2 只是测试数据恰好不同，不是 Contract 唯一性保证）
  - **新增 `CatalogEntry.entry_id: str`** = 稳定 source-local fact identity（"这条事实是谁"）——明确区分：`entry_id` = stable fact identity / `key` = retrieval / semantic lookup key / `evidence` = freshness / version evidence。固定原则：**"Fact identity ≠ freshness/version evidence."**（事实身份不等于版本 / 新鲜度证据）
  - **fact_id 最终定义**：`f"{source.name}:{entry.entry_id}"`——source-qualified entry identity；不再依赖 evidence 作 identity discriminator，不采用 content hash（内容变化 ≠ identity 变化）
  - **source uniqueness invariant**：`InMemoryMetadataSource` 构造阶段校验同一个 source snapshot 内 `entry_id` 全局唯一（跨所有 index key），重复即 fail fast——固定原则：**"Fact identity uniqueness is a source-boundary invariant."**（不在 Retriever 产生 duplicate fact_id 后才补救）
  - **fixture 更新**：分配稳定 entry_id——`schema.orders` / `metric.gmv` / `region.east_china` / `metric.sales_definition.a` / `metric.sales_definition.b`（deterministic / 可读 / 不依赖 object identity / 不依赖随机 UUID / 不依赖 criteria 顺序 / 不把 evidence 当 identity）
  - **identity / evidence 分离测试（4 项新增）**：同 key + 同 evidence + 不同 entry_id → fact_id 不同（evidence 不承担唯一身份）/ 重复 entry_id → source construction fail fast / ambiguous candidates 每 candidate 唯一 entry_id / fact_id（source_ref 相同但 fact_id 唯一）/ 同一 entry_id evidence revision-1 → revision-2：stable identity 仍同一事实、evidence 明确变化（representation 边界，不实现 history / version store）
  - **DTO 保持**：RetrievalReference（fact_id + source_ref + evidence）/ MaterializedFact（fact_id + content）不重复塞 entry_id——fact_id 已承担 source-qualified identity；references / materialized 分层保持；source_ref 只承担 source / lookup identity，不承担 fact-level unique identity（`catalog-v1:ambiguous_metric` 可对应多候选）
  - **Chapter 20 同步**：20.4 增加 Identity 模型四概念表 + 固定原则（删除"fact_id 由 source + key + evidence 构造"表述）；20.6 fixture entry_id 说明；20.7 Source Contract 层 2 扩展 entry_id 唯一性 + identity chain 增加 entry_id 层；20.9 evidence 增加 fact identity uniqueness / fact/evidence separation verified（未验证补充 production lineage ID scheme / global cross-system identity）；20.12 总结同步；验收 checklist 增加 identity 模型与 source_ref 职责行
  - 其它 contract 全部保持：五态 / priority / full scan / payload 策略 A / empty violation / criteria set / permutation / dedup / CatalogEntry runtime validation / source index-key identity / snapshot / fact-level binding / Node lifecycle / State 边界 / T02 fixture / T04 interface / Integration deferred
  - Evidence：**fact identity uniqueness verified + fact/evidence separation verified**（教学 fake authoritative source 的 contract-level identity）；production lineage ID scheme / global cross-system identity / production provenance schema 仍未验证
  - Gate 状态：**修正中，等待 Task Merge Gate 最终确认**；Status 仍 in_progress；不得进入 Gate D。
- 2026-08-13：**Task Merge Gate Architecture Review 已通过；最终 code-contract cleanup 已应用（feature/t03-metadata-retrieval，等待 Merge 确认）**：
  - **type annotation 修正**：`retrieval.py` 聚合中间 list 从 `list[str]` 改为 `list[MaterializedFact]`（原 annotation 与实际 append `MaterializedFact(...)` 及冻结 Contract `tuple[MaterializedFact, ...]` 漂移）——固定说明：**"ruff / pytest 通过不等于 type annotation 正确；代码 annotation 必须与已冻结 Python Contract 一致"**；不引入 mypy / pyright / 新 CI dependency
  - **fact_id encoding grammar 冻结**：`fact_id = f"{source.name}:{entry.entry_id}"`——`source_name` 与 `entry_id` 使用受限 grammar：**non-empty / trimmed / 不含 ":"**（"": 是 delimiter，含 ":" 造成 encoding 歧义）；**不静默 normalize**（identity boundary 不应改写 caller 提供的 identity，输入必须已 canonical）；教学级最小 identifier grammar，不设计 UUID / URN / global ID service / production lineage identifier
  - **validation boundary**：`CatalogEntry.__post_init__` 校验 entry_id（ValueError）；`InMemoryMetadataSource.__init__` 校验 source name（ValueError）——仍属 **source / identity contract violation**，不映射为 RetrievalOutcome
  - **grammar tests（8 项新增）**：empty / whitespace-only / untrimmed / 含 ":" 的 entry_id 拒绝；empty / untrimmed / 含 ":" 的 source name 拒绝；正常 grammar（catalog-v1 + schema.orders → fact_id=catalog-v1:schema.orders）通过
  - **Chapter 20 最小同步**：20.4 Identity 模型附近增加 fact_id encoding boundary 一句（受限 grammar 避免 delimiter ambiguity；教学级 source-qualified encoding，非 production global identity scheme）；20.9 evidence 增加 source-qualified identity string encoding 无歧义 verified（未验证补充 global uniqueness / production URI scheme，不宣称 global uniqueness / cross-system identity / production URI scheme / production lineage identity verified）
  - **Gate A/B/C/D 决策、Outcome、priority、payload policy、provenance model、integration status 全部未改**
  - Gate 状态：**Task Merge Gate Architecture Review 通过；等待 Merge 确认**；Status 仍 in_progress。
