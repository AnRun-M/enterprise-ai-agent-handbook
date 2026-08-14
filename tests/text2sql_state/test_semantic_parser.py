"""T02 fake semantic parser 测试：四态 outcome、四语义状态可区分、确定性、无污染。"""

from __future__ import annotations

import pytest

from examples.text2sql_state.semantic_parser import FakeSemanticParser
from examples.text2sql_state.semantic_types import (
    IntentOutcome,
    SemanticState,
)

PARSER = FakeSemanticParser()


# ---------------------------------------------------------------- COMPLETE

def test_complete_interpretation() -> None:
    result = PARSER.parse("查询昨天的GMV")
    assert result.outcome is IntentOutcome.COMPLETE
    assert result.metric.state is SemanticState.RESOLVED
    assert result.metric.resolved == "GMV"
    assert result.time_range.state is SemanticState.RESOLVED
    assert result.time_range.resolved == "yesterday"
    assert result.query_intent.state is SemanticState.RESOLVED
    assert result.query_intent.resolved == "query"
    # 未提及的可选类别 = not applicable（不是 unresolved）
    for value in (result.entity, result.filters, result.dimension,
                  result.aggregation_intent):
        assert value.state is SemanticState.NOT_APPLICABLE


def test_complete_does_not_require_optional_categories() -> None:
    # Gate A："Optional semantic field absence is not automatically
    # partial interpretation."——"查询GMV" 没提时间，仍是 COMPLETE
    result = PARSER.parse("查询GMV")
    assert result.outcome is IntentOutcome.COMPLETE
    assert result.time_range.state is SemanticState.NOT_APPLICABLE
    assert result.metric.resolved == "GMV"


# ---------------------------------------------------------------- PARTIAL

def test_partial_time_expression_unresolved() -> None:
    # Gate A canonical PARTIAL 例："metric 已定、time expression 未解析"
    result = PARSER.parse("查询上周五的GMV")
    assert result.outcome is IntentOutcome.PARTIAL
    assert result.metric.state is SemanticState.RESOLVED
    assert result.time_range.state is SemanticState.REQUIRED_UNRESOLVED


def test_partial_query_intent_unresolved() -> None:
    # 无查询动词：无法确定 query intent → required-unresolved → PARTIAL
    result = PARSER.parse("GMV")
    assert result.outcome is IntentOutcome.PARTIAL
    assert result.query_intent.state is SemanticState.REQUIRED_UNRESOLVED
    assert result.metric.state is SemanticState.RESOLVED


def test_partial_metric_unresolved() -> None:
    # 查询请求但未识别出 metric → required-unresolved → PARTIAL
    result = PARSER.parse("查询华东")
    assert result.outcome is IntentOutcome.PARTIAL
    assert result.metric.state is SemanticState.REQUIRED_UNRESOLVED
    assert result.entity.state is SemanticState.RESOLVED


# ---------------------------------------------------------------- AMBIGUOUS

def test_ambiguous_metric_candidates() -> None:
    # Gate A canonical ambiguity 例："销售额" → GMV / paid amount / net revenue
    result = PARSER.parse("查询销售额")
    assert result.outcome is IntentOutcome.AMBIGUOUS
    assert result.metric.state is SemanticState.AMBIGUOUS_CANDIDATES
    assert result.metric.resolved is None  # 无单一 resolved 值可被静默选择
    assert result.metric.candidates == ("GMV", "paid_amount", "net_revenue")


def test_ambiguous_takes_precedence_over_partial() -> None:
    # 推导优先级（唯一规则）：AMBIGUOUS > PARTIAL——
    # 请求存在歧义（销售额）时即使 time 也 unresolved，outcome 仍是 AMBIGUOUS
    result = PARSER.parse("查询上周五的销售额")
    assert result.outcome is IntentOutcome.AMBIGUOUS
    assert result.metric.state is SemanticState.AMBIGUOUS_CANDIDATES
    assert result.time_range.state is SemanticState.REQUIRED_UNRESOLVED


# ---------------------------------------------------------------- UNSUPPORTED

def test_unsupported_request_returns_full_intent_result() -> None:
    # Gate A："Expected semantic outcomes always produce an IntentResult."
    # UNSUPPORTED 不是 None，是完整 IntentResult
    result = PARSER.parse("帮我删除数据")
    assert result.outcome is IntentOutcome.UNSUPPORTED
    assert result.unsupported_reason is not None
    assert result.unsupported_reason.startswith("unsupported request intent")
    # UNSUPPORTED 不携带任何类别语义
    for value in (
        result.metric,
        result.dimension,
        result.entity,
        result.time_range,
        result.filters,
        result.aggregation_intent,
        result.query_intent,
    ):
        assert value.state is SemanticState.NOT_APPLICABLE
    # UNSUPPORTED 默认不产生普通 downstream retrieval requirements
    assert result.retrieval_requirements == ()


@pytest.mark.parametrize(
    "question",
    ["删除订单", "修改订单状态", "导出报表", "更新数据"],
)
def test_unsupported_verbs(question: str) -> None:
    result = PARSER.parse(question)
    assert result.outcome is IntentOutcome.UNSUPPORTED


# ---------------------------------------------------------------- 四语义状态可区分

def test_resolved_and_ambiguous_candidates_distinguishable() -> None:
    result = PARSER.parse("查询昨天的销售额")
    assert result.metric.state is SemanticState.AMBIGUOUS_CANDIDATES
    assert result.time_range.state is SemanticState.RESOLVED
    # outcome 承载歧义：metric 有候选 → AMBIGUOUS
    assert result.outcome is IntentOutcome.AMBIGUOUS


def test_required_unresolved_and_not_applicable_distinguishable() -> None:
    # 同一类别（time_range）：提到但未解析 vs 根本没提——
    # Gate A："not applicable vs required but unresolved 必须可区分"
    with_time = PARSER.parse("查询上周五的GMV")
    without_time = PARSER.parse("查询GMV")
    assert with_time.time_range.state is SemanticState.REQUIRED_UNRESOLVED
    assert without_time.time_range.state is SemanticState.NOT_APPLICABLE
    assert with_time.outcome is IntentOutcome.PARTIAL
    assert without_time.outcome is IntentOutcome.COMPLETE


def test_all_four_semantic_states_expressible() -> None:
    # 四个状态都在同一 grammar 内可产生：
    resolved = PARSER.parse("查询昨天的GMV")
    ambiguous = PARSER.parse("查询销售额")
    unresolved = PARSER.parse("查询上周五的GMV")
    not_applicable = PARSER.parse("查询GMV")
    assert resolved.metric.state is SemanticState.RESOLVED
    assert ambiguous.metric.state is SemanticState.AMBIGUOUS_CANDIDATES
    assert unresolved.time_range.state is SemanticState.REQUIRED_UNRESOLVED
    assert not_applicable.time_range.state is SemanticState.NOT_APPLICABLE


# ---------------------------------------------------------------- 其它类别

def test_entity_filter_dimension_aggregation_resolved() -> None:
    result = PARSER.parse("按区域统计华东已支付的GMV总计")
    assert result.outcome is IntentOutcome.COMPLETE
    assert result.entity.resolved == "华东"
    assert result.filters.resolved == "已支付"
    assert result.dimension.resolved == "区域"
    assert result.aggregation_intent.resolved == "total"
    assert result.query_intent.resolved == "query"


# ---------------------------------------------------------------- 确定性 / 纯函数

def test_deterministic_repeated_parse() -> None:
    expected = PARSER.parse("查询华东的GMV")
    assert PARSER.parse("查询华东的GMV") == expected
    assert PARSER.parse("查询华东的GMV") == expected


def test_parser_does_not_mutate_input() -> None:
    question = "  查询昨天的GMV  "
    PARSER.parse(question)
    assert question == "  查询昨天的GMV  "


@pytest.mark.parametrize(
    "question",
    ["", "   ", "\t\n"],
)
def test_consumed_contract_violation(question: str) -> None:
    # 空输入是 consumed-contract violation，不是 semantic outcome
    with pytest.raises(ValueError):
        PARSER.parse(question)
