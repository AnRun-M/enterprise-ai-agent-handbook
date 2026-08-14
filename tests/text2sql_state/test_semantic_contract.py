"""T02 contract 非法组合预防测试（Gate B 设计核心）。

验证三个禁止组合在 Python representation 上**结构上不可表达**（不是靠
if/assert 在实现层补洞）：
1. outcome = COMPLETE 却仍存在 required-unresolved semantics
2. outcome = AMBIGUOUS 却静默选择 resolved candidate
3. outcome = UNSUPPORTED 却自动生成普通 RetrievalCriteria
"""

from __future__ import annotations

import pytest

from examples.text2sql_state.retrieval_adapter import build_retrieval_criteria
from examples.text2sql_state.semantic_types import (
    IntentOutcome,
    IntentResult,
    RetrievalPurpose,
    RetrievalRequirement,
    SemanticCategory,
    SemanticState,
    SemanticValue,
)


def make_result(**overrides: SemanticValue) -> IntentResult:
    """构造一个"全部 resolved / not-applicable"的基准 IntentResult。"""
    defaults = {
        "metric": SemanticValue.make_resolved("GMV"),
        "dimension": SemanticValue.make_not_applicable(),
        "entity": SemanticValue.make_not_applicable(),
        "time_range": SemanticValue.make_resolved("yesterday"),
        "filters": SemanticValue.make_not_applicable(),
        "aggregation_intent": SemanticValue.make_not_applicable(),
        "query_intent": SemanticValue.make_resolved("query"),
    }
    defaults.update(overrides)
    return IntentResult(**defaults)


# ------------------------------------------------ 禁止组合 1：COMPLETE 含 required-unresolved

def test_outcome_is_derived_not_a_storable_field() -> None:
    # IntentResult 构造参数中没有 outcome——它由类别语义状态推导。
    # 因此 "outcome=COMPLETE 但存在 required-unresolved" 无法被构造出来。
    result = make_result(metric=SemanticValue.make_required_unresolved())
    assert result.outcome is IntentOutcome.PARTIAL


def test_any_required_unresolved_forces_partial() -> None:
    # 即使其它类别全部 resolved，一个 REQUIRED_UNRESOLVED → PARTIAL，永不 COMPLETE
    for category_field in (
        "metric",
        "dimension",
        "entity",
        "time_range",
        "filters",
        "aggregation_intent",
        "query_intent",
    ):
        result = make_result(**{category_field: SemanticValue.make_required_unresolved()})
        assert result.outcome is IntentOutcome.PARTIAL


def test_complete_only_when_nothing_unresolved() -> None:
    result = make_result()
    assert result.outcome is IntentOutcome.COMPLETE


# ------------------------------------------------ 禁止组合 2：AMBIGUOUS 静默选择 resolved candidate

def test_ambiguous_candidates_carry_no_resolved_value() -> None:
    value = SemanticValue.make_ambiguous("GMV", "paid_amount")
    assert value.state is SemanticState.AMBIGUOUS_CANDIDATES
    assert value.resolved is None  # 没有单一 resolved 值 → 无从"静默选择"
    assert len(value.candidates) >= 2


def test_ambiguous_category_forces_ambiguous_outcome() -> None:
    result = make_result(metric=SemanticValue.make_ambiguous("GMV", "paid_amount"))
    assert result.outcome is IntentOutcome.AMBIGUOUS
    # AMBIGUOUS 时类别上仍无 resolved 值
    assert result.metric.resolved is None


# ------------------------------------------------ 禁止组合 3：UNSUPPORTED 自动生成普通 RetrievalCriteria

def test_unsupported_has_empty_retrieval_requirements() -> None:
    result = IntentResult.unsupported("unsupported request intent: 删除")
    assert result.outcome is IntentOutcome.UNSUPPORTED
    assert result.retrieval_requirements == ()


def test_unsupported_adapter_returns_none_not_criteria() -> None:
    # adapter 对空 requirements 返回 None——UNSUPPORTED 永远不会得到普通
    # RetrievalCriteria（T03 对空 criteria 是 consumed-contract violation，
    # None 表示"无需检索"，由集成层决定不调用 T03）
    result = IntentResult.unsupported("unsupported request intent: 删除")
    criteria = build_retrieval_criteria(result.retrieval_requirements)
    assert criteria is None


def test_unsupported_must_not_carry_category_semantics() -> None:
    # 构造边界 fail-fast：UNSUPPORTED + 携带已解析语义 → ValueError
    with pytest.raises(ValueError):
        IntentResult(
            metric=SemanticValue.make_resolved("GMV"),
            dimension=SemanticValue.make_not_applicable(),
            entity=SemanticValue.make_not_applicable(),
            time_range=SemanticValue.make_not_applicable(),
            filters=SemanticValue.make_not_applicable(),
            aggregation_intent=SemanticValue.make_not_applicable(),
            query_intent=SemanticValue.make_not_applicable(),
            unsupported_reason="delete request",
        )


# ------------------------------------------------ SemanticValue 形状不变式（构造边界）

def test_resolved_requires_non_empty_value() -> None:
    with pytest.raises(ValueError):
        SemanticValue.make_resolved("")
    with pytest.raises(ValueError):
        SemanticValue.make_resolved("  ")


def test_ambiguous_requires_at_least_two_distinct_candidates() -> None:
    with pytest.raises(ValueError):
        SemanticValue.make_ambiguous("GMV")
    with pytest.raises(ValueError):
        SemanticValue.make_ambiguous("GMV", "GMV")


def test_ambiguous_must_not_carry_resolved() -> None:
    with pytest.raises(ValueError):
        SemanticValue(SemanticState.AMBIGUOUS_CANDIDATES, resolved="GMV",
                      candidates=("GMV", "paid_amount"))


def test_unresolved_and_not_applicable_must_not_carry_values() -> None:
    for state in (SemanticState.REQUIRED_UNRESOLVED, SemanticState.NOT_APPLICABLE):
        with pytest.raises(ValueError):
            SemanticValue(state, resolved="x")
        with pytest.raises(ValueError):
            SemanticValue(state, candidates=("a", "b"))


def test_resolved_must_not_carry_candidates() -> None:
    with pytest.raises(ValueError):
        SemanticValue(SemanticState.RESOLVED, resolved="GMV", candidates=("GMV",))


# ------------------------------------------------ outcome 优先级（唯一推导规则）

def test_outcome_priority_ambiguous_over_partial() -> None:
    # 同时存在 AMBIGUOUS_CANDIDATES 与 REQUIRED_UNRESOLVED → AMBIGUOUS
    result = make_result(
        metric=SemanticValue.make_ambiguous("GMV", "paid_amount"),
        time_range=SemanticValue.make_required_unresolved(),
    )
    assert result.outcome is IntentOutcome.AMBIGUOUS


def test_outcome_priority_unsupported_over_ambiguous() -> None:
    # UNSUPPORTED 只经 factory 构造（不携带类别语义）——优先级由派生规则保证：
    # unsupported_reason 非空即 UNSUPPORTED，任何类别状态都无法改变它
    result = IntentResult.unsupported("delete")
    assert result.outcome is IntentOutcome.UNSUPPORTED


# ------------------------------------------------ retrieval requirements 派生

def test_requirements_derived_from_states() -> None:
    complete = make_result()
    assert complete.retrieval_requirements == (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_ref="GMV",
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
    )


def test_time_resolved_does_not_produce_requirement() -> None:
    # Gate A 十一节：time 的 resolved 解释是 semantic token；日历 / 时区 /
    # 新鲜度裁决属外部事实，留 T02→T03 integration 边界——不自动生成 requirement
    result = make_result()
    assert result.time_range.resolved == "yesterday"
    assert all(r.category is not SemanticCategory.TIME_RANGE
               for r in result.retrieval_requirements)


def test_ambiguous_produces_candidate_scoped_requirement() -> None:
    result = make_result(metric=SemanticValue.make_ambiguous("GMV", "paid_amount"))
    assert result.retrieval_requirements == (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_ref="GMV, paid_amount",
            purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
        ),
    )


def test_unresolved_produces_complete_interpretation_requirement() -> None:
    result = make_result(time_range=SemanticValue.make_required_unresolved())
    assert any(
        r.purpose is RetrievalPurpose.COMPLETE_INTERPRETATION
        and r.category is SemanticCategory.TIME_RANGE
        for r in result.retrieval_requirements
    )
