"""LangGraph Demo 测试：行为等价、迭代 off-by-one、错误边界、reducer、无状态污染。"""

from __future__ import annotations

import operator

import pytest

from examples.basic_langgraph.agent import LangGraphAgent
from examples.basic_langgraph.graph import build_graph
from examples.basic_langgraph.routing import route_by_next_action, route_decide_or_max
from examples.basic_langgraph.state import build_initial_state
from examples.manual_agent_loop.agent import Agent as ManualAgent
from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.models import FakeLLM
from examples.manual_agent_loop.tools import FakeSQLExecutor, FakeSQLValidator
from examples.manual_agent_loop.types import (
    ActionType,
    AgentAction,
    AgentStatus,
    ToolResult,
    ValidationResult,
)

QUESTION = "查询昨天的 GMV"


def make_graph_agent(
    config: AgentConfig | None = None,
    model: FakeLLM | None = None,
    validator: FakeSQLValidator | None = None,
    executor: FakeSQLExecutor | None = None,
) -> LangGraphAgent:
    return LangGraphAgent(config=config, model=model, validator=validator, executor=executor)


class AlwaysRejectValidator(FakeSQLValidator):
    """测试专用：每一轮校验都失败，用于验证最大迭代终止。"""

    def validate(self, sql: str) -> ValidationResult:
        return ValidationResult(ok=False, error="always fails", rule="fake")


class FailingExecutor(FakeSQLExecutor):
    """测试专用：执行总是失败。"""

    def execute(self, sql: str) -> ToolResult:
        return ToolResult(ok=False, error="executor exploded")


class ExplodingModel(FakeLLM):
    """测试专用：生成 SQL 时抛出异常。"""

    def generate_sql(self, state: object) -> str:
        raise RuntimeError("model exploded")


class FinalizeFirstModel(FakeLLM):
    """测试专用：第一轮决策 FINALIZE（模型拥有决策权，即使当前没有候选 SQL）。"""

    def decide_next(self, state: object) -> AgentAction:
        if state.iteration == 0:  # type: ignore[attr-defined]
            return AgentAction(ActionType.FINALIZE, reason="forced finalize")
        return super().decide_next(state)


class FixFirstModel(FakeLLM):
    """测试专用：第一轮决策 FIX_SQL。"""

    def decide_next(self, state: object) -> AgentAction:
        if state.iteration == 0:  # type: ignore[attr-defined]
            return AgentAction(ActionType.FIX_SQL, reason="forced fix")
        return super().decide_next(state)


class ExplodingFixModel(FakeLLM):
    """测试专用：第二轮（修复）抛出异常。"""

    def fix_sql(self, state: object) -> str:
        raise RuntimeError("fix exploded")


# ---------------------------------------------------------------- 默认流程

def test_default_flow_success() -> None:
    state = make_graph_agent().invoke(QUESTION)
    assert state["status"] is AgentStatus.SUCCESS
    assert state["iteration"] == 3
    assert state["final_answer"] is not None
    assert "1,234,567.89" in state["final_answer"]


def test_first_round_fails_then_fixed() -> None:
    state = make_graph_agent().invoke(QUESTION)
    assert state["history"][0].validation_error == "missing LIMIT clause"
    assert state["history"][1].validation_error is None
    assert "LIMIT 1000" in state["current_sql"]


# ---------------------------------------------------------------- 行为等价

def test_final_sql_equals_manual() -> None:
    graph = make_graph_agent().invoke(QUESTION)
    manual = ManualAgent(config=AgentConfig()).invoke(QUESTION)
    assert graph["current_sql"] == manual.current_sql


def test_final_answer_equals_manual() -> None:
    graph = make_graph_agent().invoke(QUESTION)
    manual = ManualAgent(config=AgentConfig()).invoke(QUESTION)
    assert graph["final_answer"] == manual.final_answer


def test_execution_result_equals_manual() -> None:
    graph = make_graph_agent().invoke(QUESTION)
    manual = ManualAgent(config=AgentConfig()).invoke(QUESTION)
    assert graph["execution_result"] is not None
    assert manual.execution_result is not None
    assert graph["execution_result"].ok == manual.execution_result.ok
    assert graph["execution_result"].data == manual.execution_result.data


def test_history_action_sequence_equivalent() -> None:
    graph = make_graph_agent().invoke(QUESTION)
    manual = ManualAgent(config=AgentConfig()).invoke(QUESTION)
    graph_actions = [e.action for e in graph["history"]]
    manual_actions = [e.action for e in manual.history]
    assert graph_actions == manual_actions == [
        ActionType.GENERATE_SQL,
        ActionType.FIX_SQL,
        ActionType.FINALIZE,
    ]


def test_direct_equivalence_with_manual() -> None:
    """直接对照测试：两个实现的关键字段语义等价。"""
    config = AgentConfig()
    graph = make_graph_agent(config=config).invoke(QUESTION)
    manual = ManualAgent(config=config).invoke(QUESTION)

    assert graph["status"] is manual.status
    assert graph["current_sql"] == manual.current_sql
    assert graph["execution_result"] is not None and manual.execution_result is not None
    assert graph["execution_result"].data == manual.execution_result.data
    assert graph["final_answer"] == manual.final_answer
    assert graph["iteration"] == manual.iteration
    assert [e.action for e in graph["history"]] == [e.action for e in manual.history]


# ---------------------------------------------------------------- 迭代语义

def test_max_iterations_2_stops_before_finalize() -> None:
    config = AgentConfig(max_iterations=2)
    state = make_graph_agent(
        config=config,
        validator=AlwaysRejectValidator(config),
    ).invoke(QUESTION)

    assert state["status"] is AgentStatus.MAX_ITERATIONS_REACHED
    assert state["iteration"] == 2
    # 关键：max_iterations=2 时 finalize 不得执行
    actions = [e.action for e in state["history"]]
    assert ActionType.FINALIZE not in actions
    assert state["final_answer"] is None


def test_no_extra_rounds_after_success() -> None:
    state = make_graph_agent().invoke(QUESTION)
    assert state["status"] is AgentStatus.SUCCESS
    assert len(state["history"]) == 3  # 恰好 3 轮，SUCCESS 后没有继续执行


# ---------------------------------------------------------------- 错误边界

def test_executor_failure_saves_failure_reason() -> None:
    state = make_graph_agent(executor=FailingExecutor()).invoke(QUESTION)
    assert state["status"] is AgentStatus.FAILED
    assert state["failure_reason"] == "execution failed: executor exploded"


def test_model_exception_saves_failure_reason() -> None:
    state = make_graph_agent(model=ExplodingModel(AgentConfig())).invoke(QUESTION)
    assert state["status"] is AgentStatus.FAILED
    assert state["failure_reason"] is not None
    assert "model exploded" in state["failure_reason"]


# ---------------------------------------------------------------- 模型决策语义

def test_model_decision_finalize_is_routed() -> None:
    """模型决定 FINALIZE 就必须路由到 finalize（即使没有候选 SQL，也不改道 generate）。"""
    state = make_graph_agent(model=FinalizeFirstModel(AgentConfig())).invoke(QUESTION)

    assert state["status"] is AgentStatus.FAILED
    assert state["failure_reason"] == "cannot finalize without a SQL candidate"
    assert state["iteration"] == 1
    assert state["history"][-1].action is ActionType.FINALIZE


def test_model_decision_fix_is_routed() -> None:
    """模型决定 FIX_SQL 就必须路由到 fix_sql 节点。"""
    state = make_graph_agent(model=FixFirstModel(AgentConfig())).invoke(QUESTION)

    assert state["history"][0].action is ActionType.FIX_SQL


def test_fix_exception_preserves_state_and_history() -> None:
    """第二轮 fix_sql 抛异常：iteration / history / current_sql 必须保留。"""
    state = make_graph_agent(model=ExplodingFixModel(AgentConfig())).invoke(QUESTION)

    assert state["status"] is AgentStatus.FAILED
    assert state["iteration"] == 2  # 失败发生在第 2 轮
    assert "fix exploded" in (state["failure_reason"] or "")
    # 第一轮 history 保留
    assert len(state["history"]) == 2
    assert state["history"][0].action is ActionType.GENERATE_SQL
    assert state["history"][0].validation_error == "missing LIMIT clause"
    # current_sql 保留为第一轮生成的 SQL（修复未执行成功）
    assert state["current_sql"] is not None
    assert "LIMIT" not in state["current_sql"]
    # 最后一条为失败事件
    assert state["history"][-1].status is AgentStatus.FAILED
    assert state["history"][-1].action is None


def test_model_exception_equivalent_to_manual() -> None:
    """模型异常场景与 manual_agent_loop 的关键状态语义对照。"""
    config = AgentConfig()
    graph = make_graph_agent(model=ExplodingModel(config)).invoke(QUESTION)
    manual = ManualAgent(config=config, model=ExplodingModel(config)).invoke(QUESTION)

    assert graph["status"] is AgentStatus.FAILED
    assert manual.status is AgentStatus.FAILED
    assert "model exploded" in (graph["failure_reason"] or "")
    assert "model exploded" in (manual.failure_reason or "")
    assert graph["iteration"] == manual.iteration == 1


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE orders",
        "SELECTED something",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "",
    ],
)
def test_executor_rejects_unsafe_sql(sql: str) -> None:
    assert not FakeSQLExecutor().execute(sql).ok


# ---------------------------------------------------------------- 状态卫生

def test_no_cross_invoke_pollution() -> None:
    agent = make_graph_agent()
    first = agent.invoke(QUESTION)
    second = agent.invoke(QUESTION)
    assert first["status"] is AgentStatus.SUCCESS
    assert second["status"] is AgentStatus.SUCCESS
    assert first["iteration"] == second["iteration"] == 3
    assert len(first["history"]) == len(second["history"]) == 3
    assert first["final_answer"] == second["final_answer"]


def test_router_decide_or_max_is_pure() -> None:
    state = build_initial_state(QUESTION, max_iterations=2)
    state["iteration"] = 1
    before = dict(state)
    assert route_decide_or_max(state) == "decide"
    assert state == before  # 纯函数：调用后输入 State 不被修改

    state["iteration"] = 2
    assert route_decide_or_max(state) == "max_iterations"

    state["status"] = AgentStatus.FAILED
    assert route_decide_or_max(state) == "end"  # 终止状态守卫：不再进入下一轮


def test_router_by_next_action_is_pure() -> None:
    state = build_initial_state(QUESTION, max_iterations=3)

    state["next_action"] = ActionType.GENERATE_SQL
    assert route_by_next_action(state) == "generate_sql"
    state["next_action"] = ActionType.FIX_SQL
    assert route_by_next_action(state) == "fix_sql"
    state["next_action"] = ActionType.FINALIZE
    before = dict(state)
    assert route_by_next_action(state) == "finalize"
    assert state == before  # 纯函数：调用后输入 State 不被修改

    state["status"] = AgentStatus.FAILED
    assert route_by_next_action(state) == "end"  # 终止状态守卫：不按 next_action 分发


def test_graph_compiles_and_runs() -> None:
    config = AgentConfig()
    graph = build_graph(
        model=FakeLLM(config),
        validator=FakeSQLValidator(config),
        executor=FakeSQLExecutor(),
    )
    result = graph.invoke(build_initial_state(QUESTION, config.max_iterations))
    assert result["status"] is AgentStatus.SUCCESS


def test_initial_state_complete() -> None:
    state = build_initial_state(QUESTION, max_iterations=3)
    expected_keys = {
        "user_question",
        "max_iterations",
        "current_sql",
        "validation_error",
        "validation_rule",
        "execution_result",
        "final_answer",
        "failure_reason",
        "iteration",
        "status",
        "next_action",
        "decision_reason",
        "history",
    }
    assert set(state) == expected_keys
    assert state["iteration"] == 0
    assert state["status"] is AgentStatus.RUNNING
    assert state["history"] == []


# ---------------------------------------------------------------- reducer

def test_history_reducer_appends_without_duplicates() -> None:
    state = make_graph_agent().invoke(QUESTION)
    # 3 轮恰好 3 条事件：reducer 没有重复追加
    assert len(state["history"]) == 3


def test_reducer_semantics_operator_add() -> None:
    from examples.manual_agent_loop.types import StepEvent

    e1 = StepEvent(iteration=1, status=AgentStatus.RUNNING, action=ActionType.GENERATE_SQL)
    e2 = StepEvent(iteration=2, status=AgentStatus.RUNNING, action=ActionType.FIX_SQL)
    merged = operator.add([e1], [e2])
    assert merged == [e1, e2]  # 顺序保持追加次序
