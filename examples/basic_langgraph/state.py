"""LangGraph State schema：字段语义与 manual_agent_loop.AgentState 对齐。

Graph State 与手写版本的差异：
- 手写版本：可变 dataclass，由 Runtime 显式调用 apply_* 更新；
- Graph 版本：TypedDict，节点返回「部分状态更新」，LangGraph 按 channel 合并。

history 由多个节点追加，使用 reducer（operator.add）实现追加语义：
节点返回 [event]，LangGraph 以 old + new 合并，顺序保持追加次序。
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from examples.manual_agent_loop.types import ActionType, AgentStatus, StepEvent, ToolResult


class GraphState(TypedDict):
    """图上显式传递的状态。字段语义与 manual_agent_loop.AgentState 对齐。"""

    user_question: str
    max_iterations: int
    current_sql: str | None
    validation_error: str | None
    validation_rule: str | None
    execution_result: ToolResult | None
    final_answer: str | None
    failure_reason: str | None
    iteration: int
    status: AgentStatus
    # 模型决策输出：由 decide 节点写入，条件边只按它路由。
    next_action: ActionType | None
    decision_reason: str | None
    # history 由多个节点追加：使用 reducer（operator.add）合并。
    history: Annotated[list[StepEvent], operator.add]


def build_initial_state(user_question: str, max_iterations: int) -> GraphState:
    """构造完整初始状态（LangGraph 要求初始 invoke 提供全部字段）。"""
    return {
        "user_question": user_question,
        "max_iterations": max_iterations,
        "current_sql": None,
        "validation_error": None,
        "validation_rule": None,
        "execution_result": None,
        "final_answer": None,
        "failure_reason": None,
        "iteration": 0,
        "status": AgentStatus.RUNNING,
        "next_action": None,
        "decision_reason": None,
        "history": [],
    }


class StateProxy:
    """只读属性视图：把 Graph 的 dict State 以属性访问暴露给 manual 版 FakeLLM。

    原因：`examples.manual_agent_loop.models.FakeLLM` 按 AgentState（dataclass）的
    属性访问编写（如 state.current_sql），而 Graph State 是 TypedDict。
    为了「复用 FakeLLM 而不修改它」，节点通过本适配器调用模型。
    """

    def __init__(self, state: GraphState) -> None:
        self._state = state

    def __getattr__(self, name: str) -> object:
        return self._state[name]
