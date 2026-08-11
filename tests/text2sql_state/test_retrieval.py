"""T03 检索测试：contract types、fake authoritative source、deterministic retriever。

所有 criteria 均为 fixture（Proposed consumed contract，模拟未来 T02 输出——
不是 T02 最终 schema，见 retrieval_types.py docstring）。
"""

from __future__ import annotations

import dataclasses

import pytest

from examples.text2sql_state.metadata_source import InMemoryMetadataSource, build_fixture_source
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


def test_empty_criteria_is_complete() -> None:
    # 空检索条件：所需事实集合为空集，完整满足（确定性边界决定）
    result = make_retriever().retrieve(RetrievalCriteria())
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert not result.references
    assert not result.materialized.schema_facts


# ---------------------------------------------------------------- provenance

def test_provenance_source_ref_and_evidence() -> None:
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


# ---------------------------------------------------------------- determinism / 无状态污染

def test_deterministic_repeated_retrieval() -> None:
    retriever = make_retriever()
    criteria = RetrievalCriteria(keys=("orders", "gmv", "华东"))
    assert retriever.retrieve(criteria) == retriever.retrieve(criteria)


def test_source_input_not_modified_by_retrieval() -> None:
    source = build_fixture_source()
    before = source.lookup("orders")
    make_retriever(source).retrieve(RetrievalCriteria(keys=("orders", "gmv")))
    after = source.lookup("orders")
    assert after == before


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
