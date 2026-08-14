"""T02 → T03 source-specific adapter 测试：三层链路、source-agnostic 纯度、edge-scoped。

Integration evidence **edge-scoped**（Gate A 十七节）：
- IntentResult → retrieval requirements：contract-level verified（派生规则测试）
- requirements → source-specific RetrievalCriteria：adapter-level verified（本文件）
- RetrievalCriteria → T03 RetrievalResult：**edge-level verified**（仅一条
  fixture 可映射链路的教学证据；real source / compiled graph 仍 deferred）
- "retrieval requirements exists" ≠ "routing to T03 verified"——本文件只验证
  data edge，不宣称 T02 拥有路由 T03 的权限
"""

from __future__ import annotations

import pytest

from examples.text2sql_state.metadata_source import build_fixture_source
from examples.text2sql_state.retrieval import MetadataRetriever
from examples.text2sql_state.retrieval_adapter import build_retrieval_criteria
from examples.text2sql_state.retrieval_types import RetrievalCriteria, RetrievalOutcome
from examples.text2sql_state.semantic_parser import FakeSemanticParser
from examples.text2sql_state.semantic_types import (
    IntentOutcome,
    IntentResult,
    RetrievalPurpose,
    RetrievalRequirement,
    SemanticCategory,
    SemanticValue,
)

PARSER = FakeSemanticParser()
FIXTURE_RETRIEVER = MetadataRetriever(build_fixture_source())


def criteria_for(question: str) -> RetrievalCriteria | None:
    """三层链路：IntentResult → requirements → RetrievalCriteria。"""
    result = PARSER.parse(question)
    return build_retrieval_criteria(result.retrieval_requirements)


# ---------------------------------------------------------------- IntentResult → requirements（派生）

def test_complete_result_produces_verify_and_grounding_requirements() -> None:
    # "查询昨天GMV"：metric VERIFY_DEFINITION("GMV") + time RESOLVED →
    # GROUND_EXECUTION_CONTEXT("yesterday")（固定原则："Semantic resolution ≠
    # authoritative grounding completeness."——timezone / business calendar
    # 等执行上下文仍需权威 grounding）
    result = PARSER.parse("查询昨天的GMV")
    assert result.outcome is IntentOutcome.COMPLETE
    assert result.time_range.resolved == "yesterday"
    assert result.retrieval_requirements == (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("GMV",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
        RetrievalRequirement(
            category=SemanticCategory.TIME_RANGE,
            semantic_refs=("yesterday",),
            purpose=RetrievalPurpose.GROUND_EXECUTION_CONTEXT,
        ),
    )


def test_ambiguous_result_produces_candidate_scoped_requirement() -> None:
    result = PARSER.parse("查询销售额")
    assert result.retrieval_requirements == (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("GMV", "paid_amount", "net_revenue"),
            purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
        ),
    )


def test_partial_result_includes_complete_interpretation_requirement() -> None:
    result = PARSER.parse("查询上周五的GMV")
    assert result.outcome is IntentOutcome.PARTIAL
    purposes = {r.purpose for r in result.retrieval_requirements}
    assert purposes == {
        RetrievalPurpose.VERIFY_DEFINITION,
        RetrievalPurpose.COMPLETE_INTERPRETATION,
    }
    # unresolved time 不误走 GROUND_EXECUTION_CONTEXT（interpretation 缺失 ≠ 已解析待 grounding）
    assert RetrievalPurpose.GROUND_EXECUTION_CONTEXT not in purposes


# ---------------------------------------------------------------- requirements → RetrievalCriteria（adapter）

def test_adapter_maps_complete_result_to_source_keys() -> None:
    # metric → "gmv"；time grounding → "business_calendar"（fake/source-specific key）
    criteria = criteria_for("查询昨天的GMV")
    assert criteria == RetrievalCriteria(keys=("business_calendar", "gmv"))


def test_adapter_maps_without_time_to_metric_key_only() -> None:
    # 无 time（NOT_APPLICABLE）→ 不产生 grounding criteria
    criteria = criteria_for("查询GMV")
    assert criteria == RetrievalCriteria(keys=("gmv",))


def test_adapter_maps_entity_and_metric() -> None:
    criteria = criteria_for("查询华东的GMV")
    assert criteria == RetrievalCriteria(keys=("gmv", "华东"))


def test_adapter_maps_ambiguity_to_fixture_key() -> None:
    criteria = criteria_for("查询销售额")
    assert criteria == RetrievalCriteria(keys=("ambiguous_metric",))


def test_adapter_maps_partial_complete_interpretation_key() -> None:
    criteria = criteria_for("查询上周五的GMV")
    assert criteria == RetrievalCriteria(keys=("business_calendar", "gmv"))


def test_adapter_returns_none_for_empty_requirements() -> None:
    # UNSUPPORTED（及任何无 requirements 的结果）→ None，绝不自动生成普通 criteria
    assert criteria_for("帮我删除数据") is None


def test_adapter_deterministic_and_dedup() -> None:
    first = criteria_for("查询华东的GMV")
    second = criteria_for("查询华东的GMV")
    assert first == second
    # 重复 key 不重复（去重 + 排序）；criteria 排列顺序无业务语义
    requirements = (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("GMV",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
        RetrievalRequirement(
            category=SemanticCategory.ENTITY,
            semantic_refs=("华东",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("GMV",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
    )
    assert build_retrieval_criteria(requirements) == RetrievalCriteria(
        keys=("gmv", "华东")
    )


# ---------------------------------------------------------------- source-agnostic 纯度

def test_source_vocabulary_never_leaks_into_intent_result() -> None:
    # fake source lookup key vocabulary 只属于 adapter，不得进入 IntentResult：
    # 语义 ref 是 "GMV"（大写）/ "华东"，adapter 才引入 "gmv" /
    # "region.south_china" / "ambiguous_metric" / "business_calendar" 等
    # source-specific 查询键（"华东" 恰好是用户词与 fixture key 同名——
    # fixture 设计使然，不是 IntentResult 引用 source vocabulary）
    result = PARSER.parse("查询华南已支付的销售额")
    representation = repr(result)
    for source_key in (
        "region.south_china",
        "ambiguous_metric",
        "status.paid",
        "business_calendar",
        "gmv",
    ):
        assert source_key not in representation


# ---------------------------------------------------------------- integration gap fail-fast

def test_unmapped_verify_definition_ref_raises() -> None:
    requirements = (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=("unknown_metric",),
            purpose=RetrievalPurpose.VERIFY_DEFINITION,
        ),
    )
    with pytest.raises(ValueError, match="no source key vocabulary"):
        build_retrieval_criteria(requirements)


def test_unmapped_ambiguity_category_raises() -> None:
    requirements = (
        RetrievalRequirement(
            category=SemanticCategory.TIME_RANGE,
            semantic_refs=("yesterday", "today"),
            purpose=RetrievalPurpose.RESOLVE_AMBIGUITY,
        ),
    )
    with pytest.raises(ValueError, match="no source key vocabulary"):
        build_retrieval_criteria(requirements)


def test_unmapped_complete_interpretation_category_raises() -> None:
    requirements = (
        RetrievalRequirement(
            category=SemanticCategory.METRIC,
            semantic_refs=(),
            purpose=RetrievalPurpose.COMPLETE_INTERPRETATION,
        ),
    )
    with pytest.raises(ValueError, match="no source key vocabulary"):
        build_retrieval_criteria(requirements)


# ---------------------------------------------------------------- candidate 结构化保持（Review 加固八）

def test_ambiguous_candidates_preserved_through_adapter() -> None:
    # adapter 按 category 映射 ambiguous fixture key，但不得把候选集丢掉
    result = PARSER.parse("查询销售额")
    requirements = result.retrieval_requirements
    (requirement,) = requirements
    assert requirement.purpose is RetrievalPurpose.RESOLVE_AMBIGUITY
    assert requirement.semantic_refs == ("GMV", "paid_amount", "net_revenue")
    criteria = build_retrieval_criteria(requirements)
    assert criteria == RetrievalCriteria(keys=("ambiguous_metric",))
    # adapter 之后 requirement 中的候选仍然完整
    assert requirement.semantic_refs == ("GMV", "paid_amount", "net_revenue")


def test_candidates_with_commas_keep_structure() -> None:
    # 候选文本即使包含逗号，结构仍不丢失——不得因 join 变成无法区分的字符串
    candidates = ("gross, tax included", "net revenue")
    na = SemanticValue.make_not_applicable()
    structured = IntentResult(
        metric=SemanticValue.make_ambiguous(*candidates),
        dimension=na,
        entity=na,
        time_range=na,
        filters=na,
        aggregation_intent=na,
        query_intent=SemanticValue.make_resolved("query"),
    )
    (requirement,) = structured.retrieval_requirements
    assert requirement.semantic_refs == candidates
    assert requirement.semantic_refs == ("gross, tax included", "net revenue")
    # adapter 仍按 category 映射，不因候选文本含逗号而失败
    criteria = build_retrieval_criteria(structured.retrieval_requirements)
    assert criteria == RetrievalCriteria(keys=("ambiguous_metric",))


def test_adapter_does_not_modify_requirements() -> None:
    result = PARSER.parse("查询华东的GMV")
    requirements = result.retrieval_requirements
    before = requirements
    build_retrieval_criteria(requirements)
    assert requirements == before  # 输入 requirements 未被修改（frozen + 无副作用）


# ---------------------------------------------------------------- edge-scoped：RetrievalCriteria → T03 RetrievalResult

def test_edge_criteria_to_t03_retrieval_result_complete() -> None:
    """edge-scoped 教学证据：可映射链路的 criteria 可直接被 T03 消费。

    仅验证 data edge（requirements → criteria → RetrievalResult）；
    real source / compiled graph 仍 deferred；不宣称 T02 路由 T03。
    无 time 的请求：("gmv",) → T03 COMPLETE。
    """
    criteria = criteria_for("查询GMV")
    assert criteria is not None
    result = FIXTURE_RETRIEVER.retrieve(criteria)
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert any(f.content for f in result.materialized.business_rules)


def test_edge_grounding_to_t03_fact_deferred() -> None:
    """edge-scoped：grounding requirement → business_calendar criteria =
    adapter-level verified；business_calendar → real authoritative fact =
    **deferred**——当前 T03 fixture 无该 fact，T03 诚实返回 NOT_FOUND。

    不宣称 time grounding integration closed（审查项九）。
    """
    criteria = criteria_for("查询昨天的GMV")
    assert criteria == RetrievalCriteria(keys=("business_calendar", "gmv"))
    result = FIXTURE_RETRIEVER.retrieve(criteria)
    # gmv 找到（metric definition）、business_calendar 无权威事实 → PARTIAL
    assert result.outcome is RetrievalOutcome.PARTIAL
    assert any(f.content for f in result.materialized.business_rules)


def test_edge_ambiguous_criteria_to_t03_ambiguous_outcome() -> None:
    # "销售额" → adapter → "ambiguous_metric" → T03 对该 key 返回 AMBIGUOUS
    # （authoritative-source ambiguity 与 interpretation ambiguity 双层不混）
    criteria = criteria_for("查询销售额")
    assert criteria is not None
    result = FIXTURE_RETRIEVER.retrieve(criteria)
    assert result.outcome is RetrievalOutcome.AMBIGUOUS
