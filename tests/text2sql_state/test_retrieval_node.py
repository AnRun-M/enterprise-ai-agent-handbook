"""T03 Node adapter 测试：State 映射、lifecycle 边界（Review Focus）、无污染。"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus
from examples.text2sql_state.metadata_source import build_fixture_source
from examples.text2sql_state.retrieval import MetadataRetriever
from examples.text2sql_state.retrieval_node import retrieve_metadata_node
from examples.text2sql_state.retrieval_types import RetrievalCriteria, RetrievalOutcome
from examples.text2sql_state.state import Text2SQLState

FIXTURE_RETRIEVER = MetadataRetriever(build_fixture_source())


def make_state() -> Text2SQLState:
    return {
        "user_question": "查询华东 GMV",
        "normalized_question": "查询华东 GMV",
        "retrieval_result": None,
        "status": AgentStatus.RUNNING,
        "failure_reason": None,
    }


# ---------------------------------------------------------------- partial update

def test_writes_retrieval_result_only() -> None:
    state = make_state()
    update = retrieve_metadata_node(
        state, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("orders",))
    )
    assert set(update) == {"retrieval_result"}
    assert update["retrieval_result"].outcome is RetrievalOutcome.COMPLETE


def test_result_written_is_full_retrieval_result() -> None:
    # State 承载的是 RetrievalResult（outcome + references + materialized），
    # 不是 source object / repository client / runtime handle
    state = make_state()
    update = retrieve_metadata_node(
        state, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("orders", "gmv"))
    )
    result = update["retrieval_result"]
    assert result.outcome is RetrievalOutcome.COMPLETE
    assert result.references
    assert result.materialized.business_rules


# ---------------------------------------------------------------- lifecycle 边界（Review Focus）

def test_node_does_not_touch_lifecycle_fields() -> None:
    # 关键 Review Focus：T03 的 Retrieval Outcome ≠ Agent lifecycle——
    # Node 不写 status / failure_reason，不复制 T01 的 RUNNING→FAILED 规则。
    # 即使 outcome 是 NOT_FOUND / UNAVAILABLE，也不改 lifecycle。
    for keys in [("nonexistent_table",), ("broken_source",)]:
        state = make_state()
        update = retrieve_metadata_node(state, FIXTURE_RETRIEVER, RetrievalCriteria(keys=keys))
        assert set(update) == {"retrieval_result"}
        assert update["retrieval_result"].outcome in (
            RetrievalOutcome.NOT_FOUND,
            RetrievalOutcome.UNAVAILABLE,
        )
        assert state["status"] is AgentStatus.RUNNING  # 输入 State 不被修改
        assert state["failure_reason"] is None


def test_node_does_not_override_user_question_or_normalized() -> None:
    state = make_state()
    retrieve_metadata_node(state, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("orders",)))
    assert state["user_question"] == "查询华东 GMV"
    assert state["normalized_question"] == "查询华东 GMV"


# ---------------------------------------------------------------- 无状态污染

def test_does_not_modify_input_state() -> None:
    state = make_state()
    retrieve_metadata_node(state, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("orders",)))
    assert state["retrieval_result"] is None  # Node 不原地修改输入 State


def test_no_cross_invoke_pollution() -> None:
    s1 = make_state()
    s2 = make_state()
    u1 = retrieve_metadata_node(s1, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("orders",)))
    u2 = retrieve_metadata_node(s2, FIXTURE_RETRIEVER, RetrievalCriteria(keys=("broken_source",)))
    assert u1["retrieval_result"].outcome is RetrievalOutcome.COMPLETE
    assert u2["retrieval_result"].outcome is RetrievalOutcome.UNAVAILABLE
    assert s1["retrieval_result"] is None
    assert s2["retrieval_result"] is None


def test_repeated_calls_are_stable() -> None:
    state = make_state()
    criteria = RetrievalCriteria(keys=("orders", "gmv"))
    first = retrieve_metadata_node(state, FIXTURE_RETRIEVER, criteria)
    second = retrieve_metadata_node(state, FIXTURE_RETRIEVER, criteria)
    assert first == second
