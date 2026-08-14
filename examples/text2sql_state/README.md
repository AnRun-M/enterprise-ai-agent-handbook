# text2sql_state

Part 04 Text-to-SQL 实现载体（单 Python 包，标准 `import` 可导入）。

## 模块清单

| 模块 | 归属 | 说明 |
|---|---|---|
| `state.py` | 共享 | `Text2SQLState`（Part 04 图执行状态最小契约；`user_question` / `normalized_question` / `intent_result` / `retrieval_result` / `status` / `failure_reason`） |
| `normalization.py` | T01 | 输入规范化纯函数（trim / whitespace canonicalization / empty detection） |
| `normalize_node.py` | T01 | T01 Node adapter（success 只写 `normalized_question`；failure 仅 RUNNING → FAILED） |
| `semantic_types.py` | T02 | 语义解释 contract 类型：`IntentOutcome` 四态 / `SemanticState` 四语义状态 / `SemanticValue` / `IntentResult` / `RetrievalRequirement`（source-agnostic 逻辑层） |
| `semantic_parser.py` | T02 | `FakeSemanticParser`（deterministic fake parser，不接真实 LLM） |
| `semantic_node.py` | T02 | T02 Node adapter（只写 `intent_result`，不写 status/failure_reason，不调用/路由 T03） |
| `retrieval_adapter.py` | T02→T03 | source-specific adapter（source-agnostic retrieval requirements → T03 `RetrievalCriteria` fixture） |
| `metadata_source.py` | T03 | fake authoritative source（`InMemoryMetadataSource` + fixture） |
| `retrieval.py` | T03 | `MetadataRetriever`（确定性检索，读取事实不创造事实） |
| `retrieval_node.py` | T03 | T03 Node adapter（只写 `retrieval_result`，Outcome ≠ Agent lifecycle） |
| `retrieval_types.py` | T03 | 检索 contract 类型（`RetrievalOutcome` 五态 / `RetrievalCriteria`（Proposed fixture）等） |
| `validation.py` | T05 | SQL 静态校验（`RuleBasedSQLValidator` / `RULE_ORDER`） |

## 状态

- T01：completed（TASK-0032，PR #60）
- T03：completed（TASK-0033，PR #62）
- T05：completed（TASK-0030，PR #56）
- T02：Gate B/C implemented（TASK-0034，feature/t02-intent-semantic-parsing，待 Architecture + Implementation Review）

## 关键设计点（T02）

- **outcome 派生**：`IntentResult.outcome` 由类别语义状态推导（UNSUPPORTED > AMBIGUOUS > PARTIAL > COMPLETE），不可独立写入——"COMPLETE 含 required-unresolved" 结构上不可表达。
- **四语义状态可区分**：`SemanticValue` = resolved / ambiguous candidates / required-unresolved / not-applicable；AMBIGUOUS_CANDIDATES 只承载 ≥2 候选、无单一 resolved 值——"AMBIGUOUS 静默选择候选" 不可表达。
- **三层接口**：IntentResult → source-agnostic retrieval requirements（`retrieval_requirements` 派生）→ `build_retrieval_criteria`（source-specific adapter）→ T03 `RetrievalCriteria` fixture。UNSUPPORTED 的 requirements 恒为空，adapter 返回 `None`——不生成普通 RetrievalCriteria。
- **stale-state**：每次正常解析整体 overwrite `intent_result`，不依赖逐字段 invalidation。
- **integration edge-scoped**：T01→IntentResult / IntentResult→requirements / requirements→RetrievalCriteria 各 edge 独立记录，data edge ≠ routing edge。
