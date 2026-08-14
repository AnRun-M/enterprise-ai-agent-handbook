"""T02 Node adapter 测试：State 映射、lifecycle/routing 边界、stale overwrite、无污染。"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.types import AgentStatus
from examples.text2sql_state.semantic_node import parse_intent_node
from examples.text2sql_state.semantic_parser import FakeSemanticParser
from examples.text2sql_state.semantic_types import IntentOutcome, IntentResult
from examples.text2sql_state.state import Text2SQLState

PARSER = FakeSemanticParser()

_ALL_OUTCOME_QUESTIONS = [
    ("查询昨天的GMV", IntentOutcome.COMPLETE),
    ("查询上周五的GMV", IntentOutcome.PARTIAL),
    ("查询销售额", IntentOutcome.AMBIGUOUS),
    ("帮我删除数据", IntentOutcome.UNSUPPORTED),
]


def make_state(normalized: str | None = "查询昨天的GMV") -> Text2SQLState:
    return {
        "user_question": "查询昨天的GMV",
        "normalized_question": normalized,
        "intent_result": None,
        "retrieval_result": None,
        "status": AgentStatus.RUNNING,
        "failure_reason": None,
    }


# ---------------------------------------------------------------- partial update

def test_writes_intent_result_only() -> None:
    state = make_state()
    update = parse_intent_node(state, PARSER)
    assert set(update) == {"intent_result"}
    assert update["intent_result"].outcome is IntentOutcome.COMPLETE


@pytest.mark.parametrize("question,expected_outcome", _ALL_OUTCOME_QUESTIONS)
def test_all_outcomes_map_to_intent_result(
    question: str, expected_outcome: IntentOutcome
) -> None:
    # 四态 expected outcome 都产生完整 IntentResult（None 不表示任何 outcome）
    state = make_state(question)
    update = parse_intent_node(state, PARSER)
    assert update["intent_result"].outcome is expected_outcome


# ---------------------------------------------------------------- lifecycle 边界（Gate A 第 9 项）

@pytest.mark.parametrize("question,_outcome", _ALL_OUTCOME_QUESTIONS)
def test_node_does_not_touch_lifecycle_fields_for_any_outcome(
    question: str, _outcome: IntentOutcome
) -> None:
    # 关键边界：semantic outcome（四态）≠ Agent lifecycle——
    # 即使 PARTIAL / AMBIGUOUS / UNSUPPORTED 也不写 status / failure_reason
    state = make_state(question)
    update = parse_intent_node(state, PARSER)
    assert set(update) == {"intent_result"}
    assert state["status"] is AgentStatus.RUNNING  # 输入 State 不被修改
    assert state["failure_reason"] is None


def test_node_does_not_write_status_or_failure_reason_even_for_unsupported() -> None:
    # UNSUPPORTED 是 expected application outcome → clarification control flow，
    # 不是 failure；Node 不发起任何 lifecycle transition
    state = make_state("帮我删除数据")
    update = parse_intent_node(state, PARSER)
    assert set(update) == {"intent_result"}
    assert update["intent_result"].outcome is IntentOutcome.UNSUPPORTED


# ---------------------------------------------------------------- routing 边界（Gate A 第 7/9 项）

def test_node_signature_has_no_t03_dependency() -> None:
    # "Having retrieval requirements does not authorize T02 to invoke T03."
    # Node 不接收 retriever / criteria，update 中不含 retrieval_result
    import inspect

    params = inspect.signature(parse_intent_node).parameters
    assert set(params) == {"state", "parser"}
    update = parse_intent_node(make_state(), PARSER)
    assert "retrieval_result" not in update


# ---------------------------------------------------------------- SemanticParser Protocol 依赖（Review 加固九）

def test_node_depends_on_semantic_parser_protocol_not_fake() -> None:
    # Node 依赖 SemanticParser 语义契约（Protocol），不依赖 FakeSemanticParser
    # fake implementation——任何满足契约的 parser 都可注入（ch18 DI 边界）

    class StubParser:
        """最小 Protocol 实现（无 FakeSemanticParser 依赖）。"""

        def parse(self, normalized_question: str) -> IntentResult:
            return IntentResult.unsupported("stub parser")

    state = make_state("查询昨天的GMV")
    update = parse_intent_node(state, StubParser())
    assert update["intent_result"].outcome is IntentOutcome.UNSUPPORTED
    assert set(update) == {"intent_result"}


# ---------------------------------------------------------------- consumed-contract violation

def test_none_normalized_question_raises_value_error() -> None:
    # normalized_question=None 是 consumed-contract violation（ValueError），
    # 不进入 outcome taxonomy；pure parser 只收 str，Node adapter 保证契约
    state = make_state(normalized=None)
    with pytest.raises(ValueError, match="consumed-contract violation"):
        parse_intent_node(state, PARSER)


# ---------------------------------------------------------------- stale overwrite（整体替换）

def test_stale_intent_result_wholesale_replaced_by_new_result() -> None:
    # Gate A 十节：每次正常 interpretation 都返回新的完整 IntentResult
    # 整体 overwrite 上一轮——stale 值（这里注入一个 AMBIGUOUS 旧结果）
    # 被本轮完整结果整体替换，不是逐字段合并、也不是置 None
    state = make_state("查询昨天的GMV")
    state["intent_result"] = PARSER.parse("查询销售额")  # 旧一轮 AMBIGUOUS（stale）
    update = parse_intent_node(state, PARSER)
    # 模拟 Graph State 默认 merge（{**state, **update}）：整体替换
    merged = {**state, **update}
    assert merged["intent_result"] is update["intent_result"]
    assert merged["intent_result"].outcome is IntentOutcome.COMPLETE
    assert merged["intent_result"].metric.resolved == "GMV"


def test_previous_complete_replaced_by_unsupported_wholesale() -> None:
    # 上一轮 COMPLETE → 本轮 UNSUPPORTED：新 UNSUPPORTED IntentResult 整体替换
    state = make_state("帮我删除数据")
    state["intent_result"] = PARSER.parse("查询昨天的GMV")  # 上一轮 COMPLETE
    update = parse_intent_node(state, PARSER)
    merged = {**state, **update}
    assert merged["intent_result"].outcome is IntentOutcome.UNSUPPORTED
    assert merged["intent_result"] is not None  # 不是 None 表达


def test_semantics_change_between_rounds_overwrite_old_values() -> None:
    # 上一轮 metric=GMV → 本轮 metric=订单数：整体替换，无逐字段 stale
    state = make_state("查询订单数")
    state["intent_result"] = PARSER.parse("查询昨天的GMV")
    update = parse_intent_node(state, PARSER)
    merged = {**state, **update}
    assert merged["intent_result"].metric.resolved == "订单数"
    assert merged["intent_result"].time_range.state.value == "not_applicable"


# ---------------------------------------------------------------- 无状态污染

def test_does_not_modify_input_state() -> None:
    state = make_state()
    parse_intent_node(state, PARSER)
    assert state["intent_result"] is None  # Node 不原地修改输入 State


def test_no_cross_invoke_pollution() -> None:
    s1 = make_state("查询昨天的GMV")
    s2 = make_state("帮我删除数据")
    u1 = parse_intent_node(s1, PARSER)
    u2 = parse_intent_node(s2, PARSER)
    assert u1["intent_result"].outcome is IntentOutcome.COMPLETE
    assert u2["intent_result"].outcome is IntentOutcome.UNSUPPORTED
    assert s1["intent_result"] is None
    assert s2["intent_result"] is None


def test_repeated_calls_are_stable() -> None:
    state = make_state("查询华东的GMV")
    first = parse_intent_node(state, PARSER)
    second = parse_intent_node(state, PARSER)
    assert first == second
