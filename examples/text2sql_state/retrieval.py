"""T03 MetadataRetriever：确定性检索，读取事实不创造事实。

Gate A 冻结（TASK-0033）+ Gate B/C Review 修正：
- Retriever 只从权威源读取 schema facts / metadata / business rules
- LLM 不得成为事实源；无结果时不得静默生成假事实
- 输出 outcome + provenance/references + materialized facts
- 不决定继续 T04 / 终止 / retry / ask human（路由由后续应用控制流表达）

聚合规则（Gate B/C Review 修正）：
- **Outcome priority ≠ iteration short-circuit**：完整扫描所有 criteria keys，
  扫描完成后统一计算 outcome——不因 encounter order 提前返回
- **criteria 排列顺序无业务语义**：除非 contract 明确声明顺序有业务语义，
  retrieval criteria 的排列顺序不应改变逻辑检索结果（permutation-invariant）
- **UNAVAILABLE payload policy（策略 A）**：即使整体 outcome = UNAVAILABLE，
  仍保留其它可成功读取 key 的 references / materialized facts
  （与 PARTIAL"保留找到事实"理念连续）；且与 criteria 顺序无关
- outcome 唯一顺序：UNAVAILABLE > AMBIGUOUS > NOT_FOUND > PARTIAL > COMPLETE
- empty criteria = consumed-contract violation（ValueError）——
  五态只描述"合法 retrieval criteria 查询权威源后的结果"
- **fact-level provenance binding**（Task Merge Gate Review 修正）：
  同一条 entry 同时产出 RetrievalReference（fact_id + source_ref + evidence）
  与 MaterializedFact（fact_id + content），共享稳定 fact_id——
  消费者可把每一条 materialized fact 解析到它的 provenance
- **fact identity ≠ freshness/version evidence**（Task Merge Gate Review
  修正）：fact_id = source-qualified entry identity（source 名 + 稳定
  entry_id）——entry_id 承担稳定 fact identity；key 只承担 lookup 身份；
  evidence 只承担 freshness / version 证据，不承担 identity discriminator；
  不把 content 变化等同 identity 变化（同一事实的 evidence 更新仍表示
  同一事实）；entry_id 唯一性由 source construction 保证
  （metadata_source.py：source-boundary invariant）

Validation 分层（最终复审明确）：
1. **CatalogEntry construction = field runtime validation**（metadata_source.py
   `__post_init__` 运行时拒绝非 CatalogEntryKind）
2. **InMemoryMetadataSource construction = index / entry identity validation**
   （`entry.key == index_key` 构造即失败——provenance 正确性从 source
   construction 开始，不在 Retriever 输出时修补）
3. **MetadataRetriever = trusted source consumption**（本文件只读已通过
   source contract validation 的 entries）
4. **RetrievalReference = provenance output**（source_ref 只由已验证的
   entry identity 产生，不掩盖 mismatch）
5. **Retriever 内未知 kind 的 else = defensive impossible-branch protection**
   （Enum 已封顶 + 构造已校验；不把 malformed data 拖到 materialization
   中途作为主要校验路径）

**Type annotation contract**（最终 code-contract cleanup）：
- ruff / pytest 通过不等于 type annotation 正确；代码 annotation 必须与
  已冻结 Python Contract 一致——`MaterializedFacts.schema_facts /
  business_rules` 是 `tuple[MaterializedFact, ...]`，本文件聚合时的
  中间 list 也必须标注 `list[MaterializedFact]`（不引入 mypy / pyright /
  新 CI dependency，只修正既有 annotation）

**fact_id encoding boundary**（最终 code-contract cleanup）：
- fact_id = `f"{source.name}:{entry.entry_id}"`——`source_name` 与
  `entry_id` 使用受限 grammar（**non-empty / trimmed / 不含 ":"**，
  source boundary 构造即 ValueError），使 fact_id 得到无歧义
  representation；这是**教学级 source-qualified encoding，不是
  production global identity scheme**（不宣称 global uniqueness /
  cross-system identity / production URI scheme / production lineage
  identity verified）
"""

from __future__ import annotations

from .metadata_source import CatalogEntry, CatalogEntryKind, InMemoryMetadataSource
from .retrieval_types import (
    MaterializedFact,
    MaterializedFacts,
    RetrievalCriteria,
    RetrievalOutcome,
    RetrievalReference,
    RetrievalResult,
)


class MetadataRetriever:
    """T03 确定性检索器（依赖注入：source 在构造时由应用组装，ch18）。"""

    def __init__(self, source: InMemoryMetadataSource) -> None:
        self._source = source

    @property
    def source(self) -> InMemoryMetadataSource:
        return self._source

    @staticmethod
    def _fact_id(entry: CatalogEntry, source_name: str) -> str:
        """稳定关联键：source-qualified entry identity。

        `f"{source_name}:{entry.entry_id}"`——由 source 名 + 稳定
        entry_id 构造：deterministic（纯字符串构造）/ 不依赖 object
        identity / 不依赖随机 UUID / permutation-invariant /
        duplicate-dedup 后稳定。entry_id 唯一性是 source-boundary
        不变量（metadata_source 构造即校验），因此 fact_id 在合法
        source 内必然唯一——不依赖 evidence / content 作 discriminator。
        """
        return f"{source_name}:{entry.entry_id}"

    def retrieve(self, criteria: RetrievalCriteria) -> RetrievalResult:
        """按检索条件读取事实，聚合 outcome，返回 references + materialized facts。

        只读：不修改 source、不修改 criteria（frozen dataclass）、
        无隐藏可变状态——等价 criteria（排列 / 重复 key）→ 等价 RetrievalResult。

        empty criteria：consumed-contract violation，raise ValueError——
        NOT_FOUND = 权威源对合法 criteria 明确无匹配 ≠ 调用方未提供 criteria；
        UNAVAILABLE = source operational failure ≠ invalid criteria。
        不新增第六个 RetrievalOutcome，也不滥用已有五态。
        """
        if not criteria.keys:
            raise ValueError("retrieval criteria must contain at least one key")

        # 逻辑 key set：去重（重复 key 不产生重复 facts）+ 确定性排序
        # （criteria 排列顺序无业务语义 → 排序保证 permutation-invariant）
        keys = sorted(set(criteria.keys))

        references: list[RetrievalReference] = []
        schema_facts: list[MaterializedFact] = []
        business_rules: list[MaterializedFact] = []
        missing: list[str] = []
        ambiguous = False
        unavailable = False

        for key in keys:
            lookup = self._source.lookup(key)
            if not lookup.available:
                unavailable = True  # 完整扫描，不 early return
                continue
            if not lookup.entries:
                missing.append(key)
                continue
            if len(lookup.entries) > 1:
                ambiguous = True
            for entry in lookup.entries:
                # fact-level provenance binding：同一条 entry 同时产出
                # reference（fact_id + source_ref + evidence）与
                # materialized fact（fact_id + content）——共享 fact_id
                fact_id = self._fact_id(entry, self._source.name)
                references.append(
                    RetrievalReference(
                        fact_id=fact_id,
                        source_ref=f"{self._source.name}:{entry.key}",
                        evidence=entry.evidence,
                    )
                )
                if entry.kind is CatalogEntryKind.SCHEMA:
                    schema_facts.append(
                        MaterializedFact(fact_id=fact_id, content=entry.content)
                    )
                elif entry.kind is CatalogEntryKind.BUSINESS_RULE:
                    business_rules.append(
                        MaterializedFact(fact_id=fact_id, content=entry.content)
                    )
                else:
                    # Enum 已封顶；防御性 impossible-branch protection——
                    # malformed source data 是 contract error，不是 outcome 语义
                    raise ValueError(f"unknown catalog entry kind: {entry.kind}")

        materialized = MaterializedFacts(
            schema_facts=tuple(schema_facts),
            business_rules=tuple(business_rules),
        )

        # 统一计算 outcome（优先级唯一顺序，与扫描顺序无关）
        if unavailable:
            outcome = RetrievalOutcome.UNAVAILABLE
        elif ambiguous:
            outcome = RetrievalOutcome.AMBIGUOUS
        elif not missing and references:
            outcome = RetrievalOutcome.COMPLETE
        elif missing and not references:
            outcome = RetrievalOutcome.NOT_FOUND
        else:  # 部分 key 有匹配、部分缺失
            outcome = RetrievalOutcome.PARTIAL

        return RetrievalResult(
            outcome=outcome,
            references=tuple(references),
            materialized=materialized,
        )
