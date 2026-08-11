"""T03 MetadataRetriever：确定性检索，读取事实不创造事实。

Gate A 冻结（TASK-0033）：
- Retriever 只从权威源读取 schema facts / metadata / business rules
- LLM 不得成为事实源；无结果时不得静默生成假事实
- 输出 outcome + provenance/references + materialized facts
- 不决定继续 T04 / 终止 / retry / ask human（路由由后续应用控制流表达）

Outcome 聚合规则（唯一顺序事实源，deterministic）：
1. 任一 key 的 source 不可用 → UNAVAILABLE（operational failure）
2. 任一 key 多个候选 → AMBIGUOUS（需上层澄清）
3. 全部 key 无匹配 → NOT_FOUND
4. 部分 key 无匹配 → PARTIAL（是否继续由消费方决定）
5. 全部 key 唯一匹配 → COMPLETE
"""

from __future__ import annotations

from .metadata_source import InMemoryMetadataSource
from .retrieval_types import (
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

    def retrieve(self, criteria: RetrievalCriteria) -> RetrievalResult:
        """按检索条件读取事实，聚合 outcome，返回 references + materialized facts。

        只读：不修改 source、不修改 criteria（frozen dataclass）、
        无隐藏可变状态——同一 criteria 重复检索结果确定且一致。
        """
        if not criteria.keys:
            # 空检索条件：所需事实集合为空集，完整满足（确定性边界决定）
            return RetrievalResult(
                outcome=RetrievalOutcome.COMPLETE,
                references=(),
                materialized=MaterializedFacts(),
            )

        references: list[RetrievalReference] = []
        schema_facts: list[str] = []
        business_rules: list[str] = []
        missing: list[str] = []
        ambiguous = False

        for key in criteria.keys:
            lookup = self._source.lookup(key)
            if not lookup.available:
                # operational failure：无法取得权威答案——整体 UNAVAILABLE
                return RetrievalResult(
                    outcome=RetrievalOutcome.UNAVAILABLE,
                    references=tuple(references),
                    materialized=MaterializedFacts(
                        schema_facts=tuple(schema_facts),
                        business_rules=tuple(business_rules),
                    ),
                )
            if not lookup.entries:
                missing.append(key)
                continue
            if len(lookup.entries) > 1:
                ambiguous = True
            for entry in lookup.entries:
                references.append(
                    RetrievalReference(
                        source_ref=f"{self._source.name}:{entry.key}",
                        evidence=entry.evidence,
                    )
                )
                if entry.kind == "schema":
                    schema_facts.append(entry.content)
                elif entry.kind == "business_rule":
                    business_rules.append(entry.content)

        materialized = MaterializedFacts(
            schema_facts=tuple(schema_facts),
            business_rules=tuple(business_rules),
        )

        if ambiguous:
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
