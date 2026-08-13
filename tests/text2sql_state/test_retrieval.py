"""T03 检索测试：contract types、fake authoritative source、deterministic retriever。

所有 criteria 均为 fixture（Proposed consumed contract，模拟未来 T02 输出——
不是 T02 最终 schema，见 retrieval_types.py docstring）。
"""

from __future__ import annotations

import dataclasses
import itertools

import pytest

from examples.text2sql_state.metadata_source import (
    CatalogEntry,
    CatalogEntryKind,
    InMemoryMetadataSource,
    build_fixture_source,
)
from examples.text2sql_state.retrieval import MetadataRetriever
from examples.text2sql_state.retrieval_types import (
    MaterializedFact,
    RetrievalCriteria,
    RetrievalOutcome,
    RetrievalReference,
    RetrievalResult,
)

FIXTURE = build_fixture_source()


def make_retriever(source: InMemoryMetadataSource | None = None) -> MetadataRetriever:
    return MetadataRetriever(source or FIXTURE)


# ---------------------------------------------------------------- outcome 五态

def test_complete_outcome_returns_facts_and_references() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert any(
        f.content == "orders: order_id, gmv_amount, region, order_date"
        for f in result.materialized.schema_facts
    )
    assert any(
        f.content == "GMV = 已支付订单金额合计（含税），剔除退款"
        for f in result.materialized.business_rules
    )
    assert len(result.references) == 2


def test_partial_outcome_keeps_found_facts() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "nonexistent_table")))
    assert result.outcome is RetrievalOutcome.PARTIAL
    assert len(result.references) == 1  # 只有 orders 的 reference
    assert result.materialized.schema_facts  # 找到的事实仍可消费（消费方决定是否继续）


def test_not_found_outcome_no_facts_no_refs() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("nonexistent_table",)))
    assert result.outcome is RetrievalOutcome.NOT_FOUND
    assert not result.references
    assert not result.materialized.schema_facts
    assert not result.materialized.business_rules


def test_ambiguous_outcome_multiple_candidates() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("ambiguous_metric",)))
    assert result.outcome is RetrievalOutcome.AMBIGUOUS
    assert len(result.references) == 2  # 两个合法候选都带 provenance


def test_unavailable_outcome_operational_failure() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("broken_source",)))
    assert result.outcome is RetrievalOutcome.UNAVAILABLE
    assert not result.materialized.business_rules  # 不静默生成假事实


def test_unavailable_keeps_successfully_read_facts() -> None:
    # UNAVAILABLE payload policy（策略 A）：整体 outcome = UNAVAILABLE 时，
    # 仍保留其它可成功读取 key 的 references / materialized facts
    # （与 PARTIAL"保留找到事实"理念连续；且与 criteria 顺序无关）。
    result = make_retriever().retrieve(
        RetrievalCriteria(keys=("orders", "broken_source"))
    )
    assert result.outcome is RetrievalOutcome.UNAVAILABLE
    assert result.materialized.schema_facts  # orders 已成功读取
    assert len(result.references) == 1


def test_empty_criteria_is_contract_violation() -> None:
    # empty criteria = consumed-contract violation，不映射任何 outcome：
    # NOT_FOUND = 权威源对合法 criteria 明确无匹配 ≠ 调用方未提供 criteria；
    # UNAVAILABLE = source operational failure ≠ invalid criteria。
    # 不新增第六个 RetrievalOutcome，也不滥用已有五态。
    with pytest.raises(ValueError, match="at least one key"):
        make_retriever().retrieve(RetrievalCriteria())


# ---------------------------------------------------------------- provenance

def test_provenance_source_ref_and_evidence() -> None:
    # provenance identity chain（fake source contract evidence，非生产 catalog 已验证）：
    # criteria "orders" → source index "orders" → CatalogEntry.key "orders"
    # → RetrievalReference.source_ref "catalog-v1:orders"
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders",)))
    ref = result.references[0]
    assert ref.source_ref == "catalog-v1:orders"
    assert ref.evidence == "catalog-v1"  # freshness / version evidence（依 source capability）


def test_multiple_references_for_multiple_entries() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("ambiguous_metric",)))
    refs = result.references
    assert len(refs) == 2
    assert refs[0].evidence == "revision-1"
    assert refs[1].evidence == "revision-2"  # 同一 key 多候选各自带版本证据


def test_materialized_facts_separated_from_references() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders",)))
    # references 只承载 fact_id + source_ref + evidence（无事实内容）
    for ref in result.references:
        assert ref.fact_id
        assert ref.source_ref
        assert ref.evidence
    # materialized 只承载 fact_id + content（无 source_ref / evidence）
    schema_fact = result.materialized.schema_facts[0]
    assert schema_fact.content == "orders: order_id, gmv_amount, region, order_date"
    assert "catalog-v1:orders" not in schema_fact.content


def test_references_frozen_and_immutable() -> None:
    ref = RetrievalReference(fact_id="f", source_ref="s", evidence="e")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.source_ref = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------- fact-level provenance binding

def _find_reference(result: RetrievalResult, fact: MaterializedFact) -> RetrievalReference:
    bound = [ref for ref in result.references if ref.fact_id == fact.fact_id]
    assert len(bound) == 1  # 每条 fact 有唯一可解析 binding
    return bound[0]


def test_every_fact_binds_to_exactly_one_reference() -> None:
    # 目标不是"result 有 references"，而是"每个 materialized fact 都能
    # 关联到它的 provenance"
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    facts = (*result.materialized.schema_facts, *result.materialized.business_rules)
    assert len(facts) == 2
    for fact in facts:
        ref = _find_reference(result, fact)
        assert ref.fact_id == fact.fact_id


def test_schema_and_business_rule_facts_bind_to_correct_source() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    schema_ref = _find_reference(result, result.materialized.schema_facts[0])
    rule_ref = _find_reference(result, result.materialized.business_rules[0])
    assert schema_ref.source_ref == "catalog-v1:orders"
    assert rule_ref.source_ref == "catalog-v1:gmv"


def test_binding_is_permutation_invariant() -> None:
    a = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    b = make_retriever().retrieve(RetrievalCriteria(keys=("gmv", "orders")))
    assert a == b  # fact_id 构造与 criteria 排列无关 → 完全相等含 binding


def test_ambiguous_candidates_keep_own_provenance() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("ambiguous_metric",)))
    facts = result.materialized.business_rules
    assert len(facts) == 2
    # 每个 candidate 都保留自己的 provenance（fact_id + evidence 各自唯一）
    fact_ids = {_find_reference(result, f).fact_id for f in facts}
    evidences = {_find_reference(result, f).evidence for f in facts}
    assert len(fact_ids) == 2
    assert evidences == {"revision-1", "revision-2"}


def test_duplicate_criteria_do_not_duplicate_bindings() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "orders")))
    assert len(result.references) == 1
    assert len(result.materialized.schema_facts) == 1
    assert result.references[0].fact_id == result.materialized.schema_facts[0].fact_id


def test_fact_id_is_deterministic_and_stable() -> None:
    # fact_id = source-qualified entry identity（source 名 + 稳定 entry_id）：
    # 不依赖 object identity / 随机 UUID / criteria 排列 / evidence；重复检索完全稳定
    source = build_fixture_source()
    r1 = make_retriever(source).retrieve(RetrievalCriteria(keys=("orders",)))
    r2 = make_retriever(source).retrieve(RetrievalCriteria(keys=("orders",)))
    assert r1 == r2
    assert r1.references[0].fact_id == "catalog-v1:schema.orders"


# ---------------------------------------------------------------- identity / evidence 分离（Task Merge Gate 最终复审）

def test_same_key_same_evidence_distinct_entry_ids_produce_distinct_fact_ids() -> None:
    # evidence 不承担唯一身份职责：同 key + 同 evidence 的合法 source
    # （不同内容 = 不同事实），必须产出不同 fact_id——身份由 entry_id 承担
    source = InMemoryMetadataSource(
        name="catalog",
        entries={
            "k": (
                CatalogEntry(
                    entry_id="fact.a",
                    key="k",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="口径 A",
                    evidence="v1",
                ),
                CatalogEntry(
                    entry_id="fact.b",
                    key="k",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="口径 B",
                    evidence="v1",  # 与上一条同 evidence——合法且不冲突
                ),
            ),
        },
    )
    result = make_retriever(source).retrieve(RetrievalCriteria(keys=("k",)))
    fact_ids = {ref.fact_id for ref in result.references}
    assert fact_ids == {"catalog:fact.a", "catalog:fact.b"}
    assert {ref.evidence for ref in result.references} == {"v1"}  # 双事实共享 evidence


def test_duplicate_entry_id_fails_at_source_construction() -> None:
    # fact identity uniqueness 是 source-boundary invariant：
    # 重复 entry_id（跨 index key）会在 source construction 即 fail fast，
    # 不等到 Retriever 产出 duplicate fact_id 才发现
    with pytest.raises(ValueError, match="entry_id must be unique"):
        InMemoryMetadataSource(
            name="catalog",
            entries={
                "orders": (
                    CatalogEntry(
                        entry_id="schema.orders",
                        key="orders",
                        kind=CatalogEntryKind.SCHEMA,
                        content="orders: order_id",
                        evidence="v1",
                    ),
                ),
                "gmv": (
                    CatalogEntry(
                        entry_id="schema.orders",  # 跨 key 重复 entry_id
                        key="gmv",
                        kind=CatalogEntryKind.BUSINESS_RULE,
                        content="GMV = ...",
                        evidence="v1",
                    ),
                ),
            },
        )


def test_ambiguous_candidates_have_unique_fact_ids() -> None:
    # ambiguous candidates：每 candidate 唯一 entry_id / fact_id——
    # source_ref（catalog-v1:ambiguous_metric）相同但 fact_id 不同，
    # candidate 唯一性由 fact_id 承担，不由 source_ref / evidence 承担
    result = make_retriever().retrieve(RetrievalCriteria(keys=("ambiguous_metric",)))
    refs = result.references
    assert len(refs) == 2
    assert {ref.fact_id for ref in refs} == {
        "catalog-v1:metric.sales_definition.a",
        "catalog-v1:metric.sales_definition.b",
    }
    assert {ref.source_ref for ref in refs} == {"catalog-v1:ambiguous_metric"}
    assert {ref.evidence for ref in refs} == {"revision-1", "revision-2"}


def test_fact_identity_stable_across_evidence_change() -> None:
    # 同一 entry_id，evidence 从 revision-1 → revision-2：stable identity
    # 仍表示同一事实，evidence 明确变化（representation 边界——
    # 不实现 history / version store，只验证 identity ≠ evidence）
    def make_source(evidence: str) -> InMemoryMetadataSource:
        return InMemoryMetadataSource(
            name="catalog-v1",
            entries={
                "gmv": (
                    CatalogEntry(
                        entry_id="metric.gmv",  # 同一稳定 identity
                        key="gmv",
                        kind=CatalogEntryKind.BUSINESS_RULE,
                        content="GMV = 已支付订单金额合计（含税），剔除退款",
                        evidence=evidence,
                    ),
                ),
            },
        )

    r1 = make_retriever(make_source("revision-1")).retrieve(
        RetrievalCriteria(keys=("gmv",))
    )
    r2 = make_retriever(make_source("revision-2")).retrieve(
        RetrievalCriteria(keys=("gmv",))
    )
    assert r1.references[0].fact_id == r2.references[0].fact_id == "catalog-v1:metric.gmv"
    assert r1.references[0].evidence == "revision-1"
    assert r2.references[0].evidence == "revision-2"  # evidence 变化 ≠ identity 变化


# ---------------------------------------------------------------- identifier grammar（最终 code-contract cleanup）

def _make_entry(entry_id: str) -> CatalogEntry:
    return CatalogEntry(
        entry_id=entry_id,
        key="k",
        kind=CatalogEntryKind.BUSINESS_RULE,
        content="...",
        evidence="v1",
    )


def test_empty_entry_id_rejected() -> None:
    with pytest.raises(ValueError, match="entry_id"):
        _make_entry("")


def test_whitespace_only_entry_id_rejected() -> None:
    with pytest.raises(ValueError, match="entry_id"):
        _make_entry("   ")


def test_untrimmed_entry_id_rejected() -> None:
    # 不静默 normalize：identity boundary 不应改写 caller 提供的 identity——
    # 输入必须已经 canonical（trimmed strictness）
    with pytest.raises(ValueError, match="entry_id"):
        _make_entry(" schema.orders ")


def test_entry_id_containing_colon_rejected() -> None:
    # ":" 是 fact_id 的 delimiter——entry_id 含 ":" 会造成 fact_id encoding 歧义
    with pytest.raises(ValueError, match="entry_id"):
        _make_entry("schema:orders")


def test_empty_source_name_rejected() -> None:
    with pytest.raises(ValueError, match="source name"):
        InMemoryMetadataSource(name="", entries={})


def test_untrimmed_source_name_rejected() -> None:
    with pytest.raises(ValueError, match="source name"):
        InMemoryMetadataSource(name=" catalog-v1 ", entries={})


def test_source_name_containing_colon_rejected() -> None:
    # ":" 是 fact_id 的 delimiter——source name 含 ":" 会造成 fact_id encoding 歧义
    with pytest.raises(ValueError, match="source name"):
        InMemoryMetadataSource(name="catalog:v1", entries={})


def test_fact_id_encoding_grammar_unambiguous() -> None:
    # 受限 grammar（non-empty / trimmed / 无 ":"）下 fact_id 编码无歧义：
    # source=catalog-v1 + entry_id=schema.orders → fact_id=catalog-v1:schema.orders
    source = InMemoryMetadataSource(
        name="catalog-v1",
        entries={
            "orders": (
                CatalogEntry(
                    entry_id="schema.orders",
                    key="orders",
                    kind=CatalogEntryKind.SCHEMA,
                    content="orders: order_id",
                    evidence="v1",
                ),
            ),
        },
    )
    result = make_retriever(source).retrieve(RetrievalCriteria(keys=("orders",)))
    assert result.references[0].fact_id == "catalog-v1:schema.orders"


# ---------------------------------------------------------------- determinism / permutation invariance

def test_deterministic_repeated_retrieval() -> None:
    # evidence 类型 1：同一 criteria 重复执行稳定（repeated deterministic）
    retriever = make_retriever()
    criteria = RetrievalCriteria(keys=("orders", "gmv", "华东"))
    assert retriever.retrieve(criteria) == retriever.retrieve(criteria)


def test_permutation_invariance_complete() -> None:
    # evidence 类型 2：等价 criteria 排列 → 等价 RetrievalResult（不只是 outcome 相同）
    a = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    b = make_retriever().retrieve(RetrievalCriteria(keys=("gmv", "orders")))
    assert a == b


def test_permutation_invariance_unavailable() -> None:
    a = make_retriever().retrieve(
        RetrievalCriteria(keys=("orders", "broken_source"))
    )
    b = make_retriever().retrieve(
        RetrievalCriteria(keys=("broken_source", "orders"))
    )
    assert a == b
    assert a.outcome is RetrievalOutcome.UNAVAILABLE


def test_unavailable_priority_is_permutation_invariant() -> None:
    # 含 unavailable + ambiguous + complete 三态混合：任何排列
    # outcome 必须始终 UNAVAILABLE（优先级最高），references/materialized 一致
    base = ("orders", "ambiguous_metric", "broken_source")
    results = [
        make_retriever().retrieve(RetrievalCriteria(keys=p))
        for p in itertools.permutations(base)
    ]
    assert all(r.outcome is RetrievalOutcome.UNAVAILABLE for r in results)
    assert all(r == results[0] for r in results)


def test_duplicate_keys_deduplicated() -> None:
    # RetrievalCriteria 视为逻辑 key set：重复 key 去重（不产生重复 facts / references）
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "orders")))
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert len(result.references) == 1
    assert len(result.materialized.schema_facts) == 1
    assert result.materialized.schema_facts[0].content == (
        "orders: order_id, gmv_amount, region, order_date"
    )


def test_source_input_not_modified_by_retrieval() -> None:
    source = build_fixture_source()
    before = source.lookup("orders")
    make_retriever(source).retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    after = source.lookup("orders")
    assert after == before


def test_source_rejects_entry_key_mismatch() -> None:
    # source identity contract：index_key 与 CatalogEntry.key 必须一致——
    # mismatch 会在 lookup 时造成 silent provenance corruption
    # （lookup("orders") 却产出 source_ref=catalog:customers），
    # 必须在 source construction 即 fail fast，不进入 lookup / Retriever。
    mismatched = CatalogEntry(
        entry_id="schema.customers",
        key="customers",
        kind=CatalogEntryKind.SCHEMA,
        content="...",
        evidence="v1",
    )
    with pytest.raises(ValueError, match="must match source index key"):
        InMemoryMetadataSource(
            name="catalog",
            entries={"orders": (mismatched,)},
        )


def test_source_snapshot_isolated_from_caller_container() -> None:
    # constructor copy / snapshot isolation：调用方后续修改原始 entries
    # 容器不影响 source 已建立的 read-only snapshot
    # （不是"整个对象绝对 immutable"声明——只证明 read-only source snapshot）。
    caller_entries = {
        "orders": (
            CatalogEntry(
                entry_id="schema.orders",
                key="orders",
                kind=CatalogEntryKind.SCHEMA,
                content="orders: order_id",
                evidence="v1",
            ),
        )
    }
    source = InMemoryMetadataSource(name="catalog", entries=caller_entries)
    before = source.lookup("orders")
    caller_entries["orders"] = ()  # 调用方修改原始容器
    assert source.lookup("orders") == before


def test_no_hidden_mutable_global_state() -> None:
    # 独立 source / retriever 实例结果一致且互不影响（无模块级可变状态）
    r1 = make_retriever(build_fixture_source())
    r2 = make_retriever(build_fixture_source())
    criteria = RetrievalCriteria(keys=("orders", "gmv"))
    assert r1.retrieve(criteria) == r2.retrieve(criteria)
    assert r1.retrieve(criteria) == make_retriever().retrieve(criteria)


# ---------------------------------------------------------------- 不创造事实

def test_no_silent_fallback_generates_fake_facts() -> None:
    # not_found：materialized 必须为空——不静默生成 / 兜底假事实
    result = make_retriever().retrieve(RetrievalCriteria(keys=("nonexistent_table",)))
    assert result.outcome is RetrievalOutcome.NOT_FOUND
    assert not result.materialized.schema_facts
    assert not result.materialized.business_rules


def test_no_llm_generated_facts() -> None:
    # Retriever 只从权威源读取：materialized 内容必须与 source entries 完全一致
    # （LLM 不得成为事实源——本实现无任何模型调用路径）
    source = build_fixture_source()
    result = make_retriever(source).retrieve(RetrievalCriteria(keys=("orders",)))
    entry = source.lookup("orders").entries[0]
    assert len(result.materialized.schema_facts) == 1
    assert result.materialized.schema_facts[0].content == entry.content
    assert result.materialized.business_rules == ()


# ---------------------------------------------------------------- contract 边界

def test_outcome_is_strongly_typed_enum() -> None:
    expected = {
        "complete": RetrievalOutcome.COMPLETE,
        "partial": RetrievalOutcome.PARTIAL,
        "not_found": RetrievalOutcome.NOT_FOUND,
        "ambiguous": RetrievalOutcome.AMBIGUOUS,
        "unavailable": RetrievalOutcome.UNAVAILABLE,
    }
    for value, member in expected.items():
        assert member.value == value


def test_result_has_no_routing_intent() -> None:
    # T03 只返回 outcome——不决定继续 T04 / 终止 / retry / ask human
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders",)))
    assert set(vars(result)) == {"outcome", "references", "materialized"}
    assert not hasattr(result, "next_action")
    assert not hasattr(result, "route")
    assert not hasattr(result, "should_continue")


def test_criteria_is_proposed_fixture_contract() -> None:
    # RetrievalCriteria 定位：Proposed consumed contract（fixture），
    # 模拟未来 T02 输出——不是 T02 最终 schema（docstring 锁住标识）
    assert "Proposed" in RetrievalCriteria.__doc__ or ""
    assert "fixture" in RetrievalCriteria.__doc__ or ""


# ---------------------------------------------------------------- source-contract strictness

def test_catalog_entry_kind_is_strict_enum() -> None:
    # Enum representation test：CatalogEntryKind 自身拒绝未知值（ValueError）。
    # 注意：这只是 Enum 自身严格，不是 CatalogEntry runtime contract 的
    # 唯一证据——真正的 source-contract 校验见
    # test_catalog_entry_rejects_non_enum_kind_at_construction。
    assert CatalogEntryKind("schema") is CatalogEntryKind.SCHEMA
    assert CatalogEntryKind("business_rule") is CatalogEntryKind.BUSINESS_RULE
    with pytest.raises(ValueError):
        CatalogEntryKind("unknown_typo")  # 无 string typo 静默路径


def test_catalog_entry_rejects_non_enum_kind_at_construction() -> None:
    # source-contract test：CatalogEntry 构造在 source boundary 做
    # **运行时**校验（__post_init__）——静态类型标注 ≠ 运行时契约校验；
    # malformed source data 在进入 Retriever / Retrieval Outcome 语义前 fail fast。
    with pytest.raises(TypeError, match="CatalogEntry.kind must be a CatalogEntryKind"):
        CatalogEntry(
            entry_id="schema.x",
            key="x",
            kind="unknown_typo",  # type: ignore[arg-type]
            content="...",
            evidence="v1",
        )


def test_fixture_entries_all_use_typed_kind() -> None:
    # fixture source 全部使用 Enum kind（无被静默忽略的未知 kind）
    source = build_fixture_source()
    for key in ("orders", "gmv", "华东", "ambiguous_metric"):
        for entry in source.lookup(key).entries:
            assert isinstance(entry.kind, CatalogEntryKind)


def test_schema_and_business_rule_kinds_materialize() -> None:
    # schema kind → schema_facts；business_rule kind → business_rules
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    assert len(result.materialized.schema_facts) == 1
    assert result.materialized.schema_facts[0].content == (
        "orders: order_id, gmv_amount, region, order_date"
    )
    assert len(result.materialized.business_rules) == 1
    assert result.materialized.business_rules[0].content == (
        "GMV = 已支付订单金额合计（含税），剔除退款"
    )
