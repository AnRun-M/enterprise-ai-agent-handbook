"""T01 Node adapter 测试：State 生命周期映射、partial update、无污染。"""

from __future__ import annotations

import pytest

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
    # field ownership：normalized_question 是 T01-owned derived field，
    # success 只写它；status / failure_reason 是 shared lifecycle fields，
    # T01 不在 success 时覆盖（也不覆盖 user_question）。
    state = make_state("查询昨天的 GMV")
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question"}
    assert state["user_question"] == "查询昨天的 GMV"  # user_question 不覆盖


def test_success_does_not_override_existing_lifecycle_state() -> None:
    # T01 不越权清除 shared lifecycle state：State 已处于 FAILED
    # （与 T01 无关的 failure，如 permission / metadata / execution），
    # 合法 normalization 不得把 task 恢复为 RUNNING——"FAILED → RUNNING"
    # 属于 new request / retry / application lifecycle reset 的职责，
    # 不由字符串合法性触发。
    state = {
        "user_question": "查询昨天 GMV",
        "normalized_question": None,
        "status": AgentStatus.FAILED,
        "failure_reason": "some unrelated failure",
    }
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question"}
    # 模拟默认 merge——证明 T01 不重置 shared lifecycle fields
    merged = {**state, **update}
    assert merged["normalized_question"] == "查询昨天 GMV"
    assert merged["status"] is AgentStatus.FAILED
    assert merged["failure_reason"] == "some unrelated failure"


# ---------------------------------------------------------------- failure

def test_empty_input_uses_existing_lifecycle_failure_contract() -> None:
    for question in ["", "   ", "\t\n"]:
        state = make_state(question)
        update = normalize_input_node(state)
        assert update["status"] is AgentStatus.FAILED
        assert update["failure_reason"] == _INVALID_INPUT_REASON
        # failure 显式 invalidates derived normalized_question（写入 None）
        assert update["normalized_question"] is None


def test_running_failure_touches_normalized_and_lifecycle_contract_fields() -> None:
    # RUNNING + invalid input：T01 发起 RUNNING → FAILED transition——
    # normalized_question（T01-owned，invalidates stale 值）+ status /
    # failure_reason（shared lifecycle，本次迁移暴露给 lifecycle contract）；
    # 不覆盖 user_question。
    state = make_state("")
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question", "status", "failure_reason"}
    assert state["user_question"] == ""


def test_non_running_failure_touches_only_normalized_question() -> None:
    # 已 FAILED（其它原因）+ invalid input：T01 只清自己的 derived field，
    # 不触碰 shared lifecycle（不替换已有 failure cause）。
    state = {
        "user_question": "",
        "normalized_question": None,
        "status": AgentStatus.FAILED,
        "failure_reason": "permission denied",
    }
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question"}


def test_failure_invalidates_stale_normalized_question_after_merge() -> None:
    # RUNNING + stale 派生值 + invalid input：T01-owned field 必须 invalidates
    # stale 值，并发起 RUNNING → FAILED。merge 语义（默认覆盖）：
    # "不返回字段" = "保留已有字段值"——因此必须显式写 None。
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


def test_invalid_input_does_not_override_existing_failure_cause() -> None:
    # shared lifecycle 是 transition-scoped：T01 只拥有 RUNNING → FAILED。
    # 已 FAILED（unrelated cause，如 permission denied）+ empty input →
    # T01 清自己的 normalized_question，但不得把 failure_reason 改成 T01 的原因。
    state = {
        "user_question": "",
        "normalized_question": "stale",
        "status": AgentStatus.FAILED,
        "failure_reason": "permission denied",
    }
    update = normalize_input_node(state)
    assert update == {"normalized_question": None}
    # 模拟默认 merge——existing failure cause 必须保留
    merged = {**state, **update}
    assert merged["normalized_question"] is None
    assert merged["status"] is AgentStatus.FAILED
    assert merged["failure_reason"] == "permission denied"


@pytest.mark.parametrize(
    "terminal_status",
    [AgentStatus.SUCCESS, AgentStatus.MAX_ITERATIONS_REACHED],
)
def test_invalid_input_does_not_override_terminal_status(
    terminal_status: AgentStatus,
) -> None:
    # T01 的 failure authority 明确限定在 RUNNING → FAILED；
    # SUCCESS / MAX_ITERATIONS_REACHED 等终止状态不得被 empty input 改成 FAILED。
    state = make_state("", status=terminal_status)
    update = normalize_input_node(state)
    assert set(update) == {"normalized_question"}
    assert update["normalized_question"] is None
    merged = {**state, **update}
    assert merged["status"] is terminal_status


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
    expected = {"normalized_question": "查询 昨天的 GMV"}
    state = make_state("  查询  昨天的  GMV  ")
    assert normalize_input_node(state) == expected
    assert normalize_input_node(state) == expected
