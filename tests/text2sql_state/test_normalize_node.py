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
        # failure 显式 invalidates derived normalized_question（写入 None）
        assert update["normalized_question"] is None


def test_failure_partial_update_touches_only_contract_fields() -> None:
    # partial update 边界区分 success / failure：
    # success 只写 normalized_question；failure 允许写三个字段
    # （normalized_question + status + failure_reason），但不覆盖 user_question。
    state = make_state("")
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question", "status", "failure_reason"}
    assert state["user_question"] == ""


def test_failure_invalidates_stale_normalized_question_after_merge() -> None:
    # 初始 State 已含旧派生值（如重放 / 复用执行上下文残留），随后空输入 → failure。
    # merge 语义（默认覆盖）："不返回字段" = "保留已有字段值"——因此 failure
    # update 必须显式写 None，否则 stale normalized_question 会残留并继续
    # 被后续 semantic parsing 消费。
    state = {
        "user_question": "",
        "normalized_question": "stale value",
        "status": AgentStatus.RUNNING,
        "failure_reason": None,
    }
    update = normalize_input_node(state)
    assert update["normalized_question"] is None
    assert update["status"] is AgentStatus.FAILED
    assert update["failure_reason"]
    # 模拟 Graph State 默认 merge（{**state, **update}）——证明 invalidate 真正生效
    merged = {**state, **update}
    assert merged["normalized_question"] is None


def test_failure_preserves_original_question() -> None:
    state = make_state("")
    normalize_input_node(state)
    assert state["user_question"] == ""


def test_node_handles_representative_string_inputs_without_exception() -> None:
    # 证据范围收窄：仅证明有限代表性 str samples 不抛异常；
    # 不从有限 tests 宣称"所有可能输入均无异常"（contract 与 test evidence 分开）。
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
