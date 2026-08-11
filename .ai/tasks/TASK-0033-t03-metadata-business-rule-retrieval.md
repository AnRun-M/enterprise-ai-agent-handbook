# TASK-0033：T03 元数据与业务规则检索（Gate A：Architecture / Contract）

## 元信息

| 字段 | 值 |
|---|---|
| Status | in_progress |
| Owner | AnRun-M |
| Created | 2026-08-11 |
| Updated | 2026-08-11 |
| Related ADR | ADR-0002 / ADR-0005（规则分层） |
| Related Task | TASK-0029（T03 = Wave 1）、TASK-0032（T01 Gate A，同分支规划） |
| Related Example | examples/text2sql_state（默认载体） |
| Related Principle | architecture-map（External Source of Truth / Model Context / 引用策略） |

## 定位

Wave 1 并行任务之一（T01 / T03 均无 Strong dependency）。**本轮只完成 Gate A：Architecture / Contract 冻结——不实现 Retriever。**

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

Gate A（本文件）→ 等待 Architecture Review → Gate B Implementation（text2sql_state retriever + 测试）→ Gate C → Gate D（Ch20 候选 T03 部分）→ Task Merge Gate → Gate E（等 T02/T04 进 main，deferred → closed）。

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
- 2026-08-11：**PR #59 Architecture Review 修正**（commit：docs: refine wave1 input and retrieval contracts）：Retrieval 拆 **Reference / Provenance 与 Materialized Payload 双层**（引用可持久化进 State，事实内容请求级物化）；RetrievalContext 收窄为 **Proposed umbrella contract**（不冻结大 DTO，schema 留 Implementation Gate A finalization）；**Retrieval Outcome 分层**（complete / partial / not_found / ambiguous / unavailable；partial 是否继续由消费方决定；unavailable 为 operational failure）；**Provenance 最小语义修正**（source + freshness / version evidence——version / revision / timestamp / etag / digest / snapshot id 依 source capability，不强迫所有 Source 有 version 字段）；**T03 → T04 内容桥接**（materialized facts 经 Context Builder 进 Model Context，不只给 URI/digest）；Architecture Decisions 6 项收敛。
