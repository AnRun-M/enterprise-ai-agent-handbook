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

## 四、Retrieval Result 方案评估

是否独立 `SemanticContext` / `SchemaContext` + `BusinessRuleContext` 分开 / 统一 `RetrievalContext`？

| 方案 | 形态 | authority | freshness | provenance | consumer needs | serialization | testing | partial availability |
|---|---|---|---|---|---|---|---|---|
| A. 独立 SemanticContext | 单一上下文类型 | 中 | 中 | 需内嵌 | T04 生成需要 | 中 | 中 | 需标记 |
| B. SchemaContext + BusinessRuleContext | 两类分开 | 高（来源分型） | 高 | 各带来源 | 生成与校验各自消费 | 中 | 高 | 分型表达 |
| C. 统一 RetrievalContext | 单类型 + 条目列表 | 高 | 高 | 条目级 | 单入口消费 | 高 | 高 | 条目级标记 |

**推荐方案：C（统一 `RetrievalContext`，Proposed）**——不做大 DTO，只冻结最少信息：

- **结构化条目列表**（每项：引用（ID / URI / digest）+ 类型标记（metadata / business_rule）+ 来源标识）
- **不复制完整业务事实进 State**（architecture-map 引用策略：ID / URI / version / digest / summary）
- 条目级 partial availability 表达（见六）

**Architecture Decisions Required（Gate A Review 项）**：① 统一 RetrievalContext vs 分型（推荐统一）② 是否独立类型 vs 直接 State 字段（检索结果为 T04 Context 组装来源——倾向独立契约类型 + 引用入 State，类比 T05 的 ValidationResult 独立契约）③ provenance 字段最小集（见五）。

## 五、Source of Truth 与 Provenance（冻结）

- **Source of Truth**：**Retriever 不创造业务事实**——只从 schema metadata / metric definitions / business rules / catalog / 外部权威源取得事实；**LLM 不得成为事实源**（ADR-005 规则分层：业务规则不靠模型记忆）
- **Provenance boundary（建立，不全字段强制）**：评估结果 contract 是否携带——source identifier / version-timestamp / digest / rule identifier。**必须回答**：T04 如何知道 Context 从哪里来？——**至少携带 source identifier + version（引用语义）**；digest / rule identifier 为候选（T04 消费需求确认后定）；生产治理细节（完整审计）留 Part 05

## 六、Failure Contract（冻结）

定义语义——**检索失败如何被 Runtime 看见**（不靠空串 / None 混用 / 隐式 fallback 掩盖）：

| 语义 | 含义 |
|---|---|
| metadata not found | 请求的表 / 字段元数据不存在 |
| business rule not found | 请求的口径 / 规则不存在 |
| partial context | 部分条目可用（条目级标记，见四-C） |
| source unavailable | 外部事实源不可达 |
| ambiguous mapping | 同一概念映射到多个事实（指标 / 维度歧义） |

**不实现 retry**（Part 05）；本轮只冻结失败如何结构化地进入 State / Context 组装。

## 七、Memory 边界（冻结）

- **T03 retrieval ≠ Memory**：Memory（ch07，跨执行）可以影响未来检索（如常用指标偏好），但 **authoritative metadata / business rule 仍来自 External Source of Truth**——**不得把旧对话缓存直接当业务事实**

## 八、Evidence（四列制）

- **代码事实**：text2sql_state 无 T03 代码；仓库无 catalog / retriever
- **测试事实**：无 T03 测试（尚不存在）
- **设计建议**：RetrievalContext（Proposed）/ 引用策略 / provenance 最小集 / failure 语义（本文件）
- **尚未验证**：retriever 行为；与 T02 真实串联（Integration deferred——T02 未实现）；与 T04 生成的真实消费

## 九、Review Gate（统一）

Gate A（本文件）→ 等待 Architecture Review → Gate B Implementation（text2sql_state retriever + 测试）→ Gate C → Gate D（Ch20 候选 T03 部分）→ Task Merge Gate → Gate E（等 T02/T04 进 main，deferred → closed）。

## 验收标准（Gate A 阶段）

- [x] 职责边界冻结（Metadata / Business Rule / Semantic Context / External Source of Truth / Model Context / Memory 区分；T03 只负责可信上下文检索）
- [x] T02 / T03 边界（Proposed consumed contract；不假装 T02 schema 已存在）
- [x] Retrieval Result 三方案评估 + 推荐（统一 RetrievalContext，条目级引用）
- [x] Source of Truth（Retriever 不创造事实；LLM 不得成为事实源）
- [x] Provenance boundary（至少 source identifier + version；digest / rule id 候选）
- [x] Failure Contract（5 语义；失败如何被 Runtime 看见，不靠空串 / None / 隐式 fallback）
- [x] Memory 边界（T03 ≠ Memory；authoritative 来自 External Source of Truth）
- [x] Evidence 四列制；未实现 Retriever
- [ ] 等待 Architecture Review（含 3 项 Architecture Decisions Required）

## 完成记录

- 2026-08-11：任务创建（in_progress）；Gate A 完成；等待 Architecture Review（planning/wave1-t01-t03-contracts 分支，与 T01 同分支规划）。
