"""手写 Agent Loop 行为测试：修复循环、终止条件、history、固定结果、失败原因。"""

from __future__ import annotations

import pytest

from examples.manual_agent_loop.agent import Agent
from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.models import FakeLLM
from examples.manual_agent_loop.state import AgentState
from examples.manual_agent_loop.tools import FakeSQLExecutor, FakeSQLValidator
from examples.manual_agent_loop.types import (
    ActionType,
    AgentAction,
    AgentStatus,
    ToolResult,
    ValidationResult,
)


def test_first_round_fails_second_round_fixes_and_succeeds() -> None:
    state = Agent(config=AgentConfig()).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.SUCCESS
    assert state.iteration == 3
    # 第二轮修复后的 SQL 包含 LIMIT，且校验通过。
    assert state.current_sql is not None
    assert "LIMIT 1000" in state.current_sql
    assert state.validation_error is None
    # 最终回答包含固定 GMV 数据。
    assert state.final_answer is not None
    assert "1,234,567.89" in state.final_answer


def test_returns_fixed_gmv_result() -> None:
    state = Agent(config=AgentConfig()).invoke("查询昨天的 GMV")

    assert state.execution_result is not None
    assert state.execution_result.ok
    assert state.execution_result.data == {
        "gmv": 1234567.89,
        "order_date": "2026-07-31",
        "row_count": 1,
    }


class AlwaysRejectValidator(FakeSQLValidator):
    """测试专用：让每一轮校验都失败，用于验证最大迭代次数终止。"""

    def validate(self, sql: str) -> ValidationResult:
        return ValidationResult(ok=False, error="always fails", rule="fake")


def test_max_iterations_reached() -> None:
    config = AgentConfig(max_iterations=2)
    state = Agent(
        config=config,
        validator=AlwaysRejectValidator(AgentConfig(max_iterations=2)),
    ).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.MAX_ITERATIONS_REACHED
    assert state.iteration == 2  # 恰好用完允许的 2 轮，第 3 轮进入前被终止
    assert state.final_answer is None


def test_history_records_key_events() -> None:
    state = Agent(config=AgentConfig()).invoke("查询昨天的 GMV")

    actions = [event.action for event in state.history]
    assert actions == [ActionType.GENERATE_SQL, ActionType.FIX_SQL, ActionType.FINALIZE]
    # 第一轮：生成 SQL 且校验失败；第二轮：修复后校验通过；第三轮：最终化。
    assert state.history[0].validation_error == "missing LIMIT clause"
    assert state.history[1].validation_error is None
    assert state.history[2].sql == state.current_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE orders",
        "SELECT 1; DELETE FROM orders",
        "DELETE FROM orders",
        "",
        "   ",
    ],
)
def test_executor_rejects_unsafe_sql(sql: str) -> None:
    result = FakeSQLExecutor().execute(sql)
    assert not result.ok


def test_executor_accepts_single_select_with_trailing_semicolon() -> None:
    result = FakeSQLExecutor().execute("SELECT order_date FROM orders LIMIT 1000;")
    assert result.ok
    assert result.data == FakeSQLExecutor.FIXED_RESULT


class FailingExecutor(FakeSQLExecutor):
    """测试专用：执行总是失败。"""

    def execute(self, sql: str) -> ToolResult:
        return ToolResult(ok=False, error="executor exploded")


def test_execution_failure_saves_failure_reason() -> None:
    state = Agent(config=AgentConfig(), executor=FailingExecutor()).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.FAILED
    assert state.failure_reason == "execution failed: executor exploded"


class ExplodingModel(FakeLLM):
    """测试专用：决策时抛出异常。"""

    def decide_next(self, state: AgentState) -> AgentAction:
        raise RuntimeError("model exploded")


def test_runtime_exception_saves_failure_reason() -> None:
    state = Agent(config=AgentConfig(), model=ExplodingModel(AgentConfig())).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.FAILED
    assert state.failure_reason is not None
    assert "model exploded" in state.failure_reason


class UnknownActionModel(FakeLLM):
    """测试专用：返回未知动作，触发 Runtime 的未知分支异常。"""

    def decide_next(self, state: AgentState) -> AgentAction:
        return AgentAction(type="bogus")  # type: ignore[arg-type]  # 故意构造未知动作


def test_unknown_action_saves_failure_reason() -> None:
    state = Agent(config=AgentConfig(), model=UnknownActionModel(AgentConfig())).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.FAILED
    assert state.failure_reason is not None
    assert "unknown action type" in state.failure_reason


def test_success_has_no_failure_reason() -> None:
    state = Agent(config=AgentConfig()).invoke("查询昨天的 GMV")

    assert state.status is AgentStatus.SUCCESS
    assert state.failure_reason is None


def test_state_is_pure_dataclass_no_globals() -> None:
    """状态只通过 AgentState 显式传递，模块内不依赖全局变量。"""
    state = Agent(config=AgentConfig()).invoke("查询昨天的 GMV")
    assert isinstance(state, AgentState)
    assert state.user_question == "查询昨天的 GMV"
    assert len(state.history) == 3
