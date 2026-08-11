"""T01 Node adapter 测试：State 生命周期映射、partial update、无污染。"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus
from examples.text2sql_state.normalize_node import _INVALID_INPUT_REASON, normalize_input_node
from examples.text2sql_state.state import Text2SQLState


def make_state(question: str, status: AgentStatus = AgentStatus.RUNNING) -> Text2SQLState:
    return {
        "user_question": question,
        "normalized_question": None,
        "status": status,
        "failure_reason": None,
    }


# ---------------------------------------------------------------- success

def test_normalized_question_written_and_original_preserved() -> None:
    state = make_state("  查询昨天的 GMV  ")
    update = normalize_input_node(state)
    assert update == {"normalized_question": "查询昨天的 GMV"}
    # original 不被覆盖（Normalization 不静默破坏原始事实）
    assert state["user_question"] == "  查询昨天的 GMV  "


def test_success_partial_update_does_not_touch_other_fields() -> None:
    state = make_state("查询昨天的 GMV")
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question"}  # 不覆盖 status / failure_reason / user_question


# ---------------------------------------------------------------- failure

def test_empty_input_uses_existing_lifecycle_failure_contract() -> None:
    for question in ["", "   ", "\t\n"]:
        state = make_state(question)
        update = normalize_input_node(state)
        assert update["status"] is AgentStatus.FAILED
        assert update["failure_reason"] == _INVALID_INPUT_REASON
        assert "normalized_question" not in update  # 不进入后续语义解析


def test_failure_preserves_original_question() -> None:
    state = make_state("")
    normalize_input_node(state)
    assert state["user_question"] == ""


def test_no_runtime_exception_on_any_input() -> None:
    for question in ["", "   ", "查询昨天的 GMV", "x" * 1000]:
        normalize_input_node(make_state(question))  # 不抛异常


# ---------------------------------------------------------------- 无状态污染

def test_no_cross_invoke_mutable_pollution() -> None:
    s1 = make_state("查询昨天的 GMV")
    s2 = make_state("查询前天的 GMV")
    u1 = normalize_input_node(s1)
    u2 = normalize_input_node(s2)
    assert u1["normalized_question"] == "查询昨天的 GMV"
    assert u2["normalized_question"] == "查询前天的 GMV"
    assert s1["normalized_question"] is None  # Node 不原地修改输入 State
    assert s2["normalized_question"] is None


def test_repeated_calls_are_stable() -> None:
    state = make_state("  查询  昨天的  GMV  ")
    assert normalize_input_node(state) == {"normalized_question": "查询 昨天的 GMV"}
    assert normalize_input_node(state) == {"normalized_question": "查询 昨天的 GMV"}
