"""T02 contract 非法组合预防测试（Gate B 设计核心 + Gate B/C Review 加固）。

验证三个禁止组合在 Python representation 上**结构上不可表达**（不是靠
if/assert 在实现层补洞）：
1. outcome = COMPLETE 却仍存在 required-unresolved semantics
2. outcome = AMBIGUOUS 却静默选择 resolved candidate
3. outcome = UNSUPPORTED 却自动生成普通 RetrievalCriteria

同时验证 runtime contract validation（Review 加固）：
- SemanticValue.state / RetrievalRequirement.category / purpose /
  IntentResult 七个 category 都是运行时类型校验，不是 type hint-only
- unsupported_reason invariant 由 __post_init__ 强制（factory 只是
  convenience，不是唯一 enforcement）
- RetrievalRequirement purpose + payload shape 不产生非法组合
- direct constructor 与 factory 遵守同一 contract（bypass tests）
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
    """构造一个"全部 resolved / not-applicable"的基准 IntentResult。

    默认 time_range = NOT_APPLICABLE——避免 grounding requirement 污染
    其它 requirements 断言；需要 time 语义的测试显式传入。
    """
    defaults = {
        "metric": SemanticValue.make_resolved("GMV"),
        "dimension": SemanticValue.make_not_applicable(),
        "entity": SemanticValue.make_not_applicable(),
        "time_range": SemanticValue.make_not_applicable(),
        "filters": SemanticValue.make_not_applicable(),
        "aggregation_intent": SemanticValue.make_not_applicable(),
        "query_intent": SemanticValue.make_resolved("query"),
    }
    defaults.update(overrides)
    return IntentResult(**defaults)


def make_not_applicable_result(**overrides: SemanticValue) -> IntentResult:
    """构造一个"全部 NOT_APPLICABLE"的基准 IntentResult（UNSUPPORTED 形状）。"""
    na = SemanticValue.make_not_applicable()
    return IntentResult(
        metric=na,
        dimension=na,
        entity=na,
        time_range=na,
        filters=na,
        aggregation_intent=na,
        query_intent=na,
        **overrides,
    )


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


# ------------------------------------------------ runtime contract validation（Review 加固一）

def test_semantic_value_state_runtime_type_check() -> None:
    # 禁止 malformed state（如 str）落入 REQUIRED_UNRESOLVED / NOT_APPLICABLE
    # 共用的 else 分支——"Static type annotation ≠ runtime contract validation."
    with pytest.raises(TypeError):
        SemanticValue(state="invalid", resolved=None, candidates=())


def test_intent_result_category_runtime_type_check() -> None:
    # 七个 category 必须是 SemanticValue——str / None / dict 不得进入后
    # 延迟到 outcome / retrieval_requirements 才 AttributeError
    for bad in ("GMV", None, {"state": "resolved"}):
        with pytest.raises(TypeError):
            IntentResult(
                metric=bad,  # type: ignore[arg-type]
                dimension=SemanticValue.make_not_applicable(),
                entity=SemanticValue.make_not_applicable(),
                time_range=SemanticValue.make_not_applicable(),
                filters=SemanticValue.make_not_applicable(),
                aggregation_intent=SemanticValue.make_not_applicable(),
                query_intent=SemanticValue.make_not_applicable(),
            )


def test_all_seven_categories_runtime_type_checked() -> None:
    na = SemanticValue.make_not_applicable()
    for field_name in (
        "metric",
        "dimension",
        "entity",
        "time_range",
        "filters",
        "aggregation_intent",
        "query_intent",
    ):
        kwargs = {
            "metric": na,
            "dimension": na,
            "entity": na,
            "time_range": na,
            "filters": na,
            "aggregation_intent": na,
            "query_intent": na,
        }
        kwargs[field_name] = "not a SemanticValue"  # type: ignore[assignment]
        with pytest.raises(TypeError):
            IntentResult(**kwargs)


# ------------------------------------------------ unsupported_reason invariant（Review 加固三）

def test_unsupported_reason_empty_rejected() -> None:
    # 直接 dataclass construction 绕过 factory 也必须遵守同一 contract
    with pytest.raises(ValueError):
        make_not_applicable_result(unsupported_reason="")


def test_unsupported_reason_whitespace_rejected() -> None:
    with pytest.raises(ValueError):
        make_not_applicable_result(unsupported_reason="  reason  ")


def test_direct_constructor_and_factory_share_contract() -> None:
    # factory 是 convenience，不是唯一 contract enforcement——
    # direct constructor 与 factory 对合法输入产生等价结果
    via_factory = IntentResult.unsupported("delete")
    via_constructor = make_not_applicable_result(unsupported_reason="delete")
    assert via_factory == via_constructor
    assert via_factory.outcome is IntentOutcome.UNSUPPORTED
    assert via_constructor.outcome is IntentOutcome.UNSUPPORTED


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


# ------------------------------------------------ RetrievalRequirement shape invariant（Review 加固六）

def test_requirement_category_runtime_type_check() -> None:
    with pytest.raises(TypeError):
        RetrievalRequirement(category="metric", semantic_refs=("GMV",),
                             purpose=RetrievalPurpose.VERIFY_DEFINITION)


def test_requirement_purpose_runtime_type_check() -> None:
    with pytest.raises(TypeError):
        RetrievalRequirement(category=SemanticCategory.METRIC, semantic_refs=("GMV",),
                             purpose="verify_definition")  # type: ignore[arg-type]


def test_verify_definition_requires_exactly_one_ref() -> None:
    with pytest.raises(ValueError):
        RetrievalRequirement(category=SemanticCategory.METRIC, semantic_refs=(),
                             purpose=RetrievalPurpose.VERIFY_DEFINITION)
    with pytest.raises(ValueError):
        RetrievalRequirement(category=SemanticCategory.METRIC,
                             semantic_refs=("GMV", "paid_amount"),
                             purpose=RetrievalPurpose.VERIFY_DEFINITION)


def test_resolve_ambiguity_requires_at_least_two_distinct_refs() -> None:
    with pytest.raises(ValueError):
        RetrievalRequirement(category=SemanticCategory.METRIC, semantic_refs=("GMV",),
                             purpose=RetrievalPurpose.RESOLVE_AMBIGUITY)
    with pytest.raises(ValueError):
        RetrievalRequirement(category=SemanticCategory.METRIC,
                             semantic_refs=("GMV", "GMV"),
                             purpose=RetrievalPurpose.RESOLVE_AMBIGUITY)


def test_complete_interpretation_requires_empty_refs() -> None:
    # unresolved 的语义类别由 category 表达，不得用 ref 伪装
    with pytest.raises(ValueError):
        RetrievalRequirement(category=SemanticCategory.TIME_RANGE,
                             semantic_refs=("time_range",),
                             purpose=RetrievalPurpose.COMPLETE_INTERPRETATION)
    valid = RetrievalRequirement(category=SemanticCategory.TIME_RANGE, semantic_refs=(),
                                 purpose=RetrievalPurpose.COMPLETE_INTERPRETATION)
    assert valid.semantic_refs == ()


def test_requirement_refs_must_be_non_empty_trimmed() -> None:
    # domain value 不合法（类型正确但值坏）→ ValueError
    for bad_refs in (("",), ("  GMV  ",)):
        with pytest.raises(ValueError):
            RetrievalRequirement(category=SemanticCategory.METRIC,
                                 semantic_refs=bad_refs,
                                 purpose=RetrievalPurpose.VERIFY_DEFINITION)


def test_requirement_ref_leaf_type_must_be_str() -> None:
    # wrong runtime type → TypeError（不是 ValueError）——Error taxonomy 区分
    with pytest.raises(TypeError):
        RetrievalRequirement(category=SemanticCategory.METRIC,
                             semantic_refs=(None,),
                             purpose=RetrievalPurpose.VERIFY_DEFINITION)


# ------------------------------------------------ runtime payload contract（最终复审闭合）

def test_resolved_payload_must_be_str() -> None:
    # RESOLVED 分支的 .strip() 不得因非 str payload 延迟成 AttributeError
    with pytest.raises(TypeError):
        SemanticValue(SemanticState.RESOLVED, resolved=123, candidates=())


def test_candidates_container_must_be_tuple() -> None:
    # mutable list 不得进入 frozen dataclass（container shape 是 runtime invariant）
    with pytest.raises(TypeError):
        SemanticValue(SemanticState.AMBIGUOUS_CANDIDATES, resolved=None,
                      candidates=["GMV", "paid_amount"])


def test_candidate_leaf_type_must_be_str() -> None:
    with pytest.raises(TypeError):
        SemanticValue(SemanticState.AMBIGUOUS_CANDIDATES, resolved=None,
                      candidates=("GMV", 123))


def test_semantic_refs_container_must_be_tuple() -> None:
    with pytest.raises(TypeError):
        RetrievalRequirement(category=SemanticCategory.METRIC,
                             purpose=RetrievalPurpose.VERIFY_DEFINITION,
                             semantic_refs=["GMV"])


def test_semantic_ref_leaf_type_must_be_str() -> None:
    with pytest.raises(TypeError):
        RetrievalRequirement(category=SemanticCategory.METRIC,
                             purpose=RetrievalPurpose.VERIFY_DEFINITION,
                             semantic_refs=("GMV", 123))


def test_unsupported_reason_leaf_type_must_be_str() -> None:
    # int.strip() 不得出现——非 None 且非 str → TypeError
    with pytest.raises(TypeError):
        make_not_applicable_result(unsupported_reason=123)


def test_legal_payloads_use_tuple_containers() -> None:
    # immutability regression：合法 candidates / semantic_refs 均为 tuple，
    # 不接受 mutable list representation（无需证明 Python 深度 immutable）
    value = SemanticValue.make_ambiguous("GMV", "paid_amount")
    assert isinstance(value.candidates, tuple)
    requirement = RetrievalRequirement(
        category=SemanticCategory.METRIC,
        purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
        semantic_refs=("GMV", "paid_amount"),
    )
    assert isinstance(requirement.semantic_refs, tuple)
    resolved = SemanticValue.make_resolved("GMV")
    assert isinstance(resolved.candidates, tuple)


# ------------------------------------------------ candidate 结构化保持（Review 加固五、八）

def test_ambiguous_requirement_preserves_structured_candidates() -> None:
    # 结构化候选不得被 flatten 成展示字符串——
    # "Structured candidate semantics must remain structured across contract
    # boundaries."
    candidates = ("gross, tax included", "net revenue")
    result = make_result(metric=SemanticValue.make_ambiguous(*candidates))
    (requirement,) = result.retrieval_requirements
    assert requirement.purpose is RetrievalPurpose.RESOLVE_AMBIGUITY
    assert requirement.semantic_refs == candidates  # 原样 tuple，未 join
    assert requirement.semantic_refs == ("gross, tax included", "net revenue")


def test_duplicate_candidates_rejected_by_semantic_value_contract() -> None:
    # duplicate candidate 仍由 SemanticValue contract 拒绝（Review 八-3）
    with pytest.raises(ValueError):
        SemanticValue.make_ambiguous("GMV", "GMV", "paid_amount")


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
            semantic_refs=("GMV",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
    )


def test_time_resolved_produces_grounding_requirement() -> None:
    # 固定原则："Semantic resolution ≠ authoritative grounding completeness."
    # time_range = RESOLVED("yesterday") 表示 T02 已唯一理解"昨天"；但
    # timezone / business calendar 等执行上下文仍可能需要 authoritative
    # grounding——产生 GROUND_EXECUTION_CONTEXT requirement，
    # **outcome 不因此变 PARTIAL**（缺的是 grounding，不是 interpretation）
    result = make_result(time_range=SemanticValue.make_resolved("yesterday"))
    assert result.time_range.state is SemanticState.RESOLVED
    assert result.time_range.resolved == "yesterday"
    assert result.outcome is IntentOutcome.COMPLETE
    assert RetrievalRequirement(
        category=SemanticCategory.TIME_RANGE,
        purpose=RetrievalPurpose.GROUND_EXECUTION_CONTEXT,
        semantic_refs=("yesterday",),
    ) in result.retrieval_requirements


def test_not_applicable_time_produces_no_grounding_requirement() -> None:
    # NOT_APPLICABLE time（根本没提时间）不产生 grounding requirement
    result = make_result()
    assert result.time_range.state is SemanticState.NOT_APPLICABLE
    assert all(
        r.category is not SemanticCategory.TIME_RANGE
        for r in result.retrieval_requirements
    )


def test_ground_execution_context_requires_exactly_one_ref() -> None:
    with pytest.raises(ValueError):
        RetrievalRequirement(
            category=SemanticCategory.TIME_RANGE,
            purpose=RetrievalPurpose.GROUND_EXECUTION_CONTEXT,
            semantic_refs=(),
        )
    with pytest.raises(ValueError):
        RetrievalRequirement(
            category=SemanticCategory.TIME_RANGE,
            purpose=RetrievalPurpose.GROUND_EXECUTION_CONTEXT,
            semantic_refs=("yesterday", "today"),
        )
    valid = RetrievalRequirement(
        category=SemanticCategory.TIME_RANGE,
        purpose=RetrievalPurpose.GROUND_EXECUTION_CONTEXT,
        semantic_refs=("yesterday",),
    )
    assert valid.semantic_refs == ("yesterday",)


def test_ambiguous_produces_candidate_scoped_requirement() -> None:
    result = make_result(metric=SemanticValue.make_ambiguous("GMV", "paid_amount"))
    assert result.retrieval_requirements == (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("GMV", "paid_amount"),
            purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
        ),
    )


def test_unresolved_produces_complete_interpretation_requirement() -> None:
    result = make_result(time_range=SemanticValue.make_required_unresolved())
    assert result.time_range.state is SemanticState.REQUIRED_UNRESOLVED
    (requirement,) = [
        r for r in result.retrieval_requirements
        if r.purpose is RetrievalPurpose.COMPLETE_INTERPRETATION
    ]
    assert requirement.category is SemanticCategory.TIME_RANGE
    assert requirement.semantic_refs == ()  # 类别由 category 表达，不伪装 ref


def test_unresolved_time_stays_complete_interpretation_not_ground() -> None:
    # 区分（审查项七）：REQUIRED_UNRESOLVED time = interpretation 本身缺失
    # → COMPLETE_INTERPRETATION；**不**误走 GROUND_EXECUTION_CONTEXT
    # （后者只用于 semantic interpretation 已 resolved 的情况）
    result = make_result(time_range=SemanticValue.make_required_unresolved())
    purposes = {r.purpose for r in result.retrieval_requirements}
    assert RetrievalPurpose.COMPLETE_INTERPRETATION in purposes
    assert RetrievalPurpose.GROUND_EXECUTION_CONTEXT not in purposes
