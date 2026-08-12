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
    RetrievalCriteria,
    RetrievalOutcome,
    RetrievalReference,
)

FIXTURE = build_fixture_source()


def make_retriever(source: InMemoryMetadataSource | None = None) -> MetadataRetriever:
    return MetadataRetriever(source or FIXTURE)


# ---------------------------------------------------------------- outcome 五态

def test_complete_outcome_returns_facts_and_references() -> None:
    result = make_retriever().retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert "orders: order_id, gmv_amount, region, order_date" in result.materialized.schema_facts
    assert "GMV = 已支付订单金额合计（含税），剔除退款" in result.materialized.business_rules
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
    # references 只承载 source_ref + evidence（无事实内容）
    for ref in result.references:
        assert ref.source_ref
        assert ref.evidence
    # materialized 只承载事实内容（无 source_ref / evidence）
    assert result.materialized.schema_facts == ("orders: order_id, gmv_amount, region, order_date",)
    assert "catalog-v1:orders" not in result.materialized.schema_facts[0]


def test_references_frozen_and_immutable() -> None:
    ref = RetrievalReference(source_ref="s", evidence="e")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.source_ref = "changed"  # type: ignore[misc]


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
    assert result.materialized.schema_facts == (
        "orders: order_id, gmv_amount, region, order_date",
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
    assert result.materialized.schema_facts == (entry.content,)
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
    assert result.materialized.schema_facts == (
        "orders: order_id, gmv_amount, region, order_date",
    )
    assert result.materialized.business_rules == (
        "GMV = 已支付订单金额合计（含税），剔除退款",
    )
