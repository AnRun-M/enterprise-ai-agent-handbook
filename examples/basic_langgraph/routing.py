"""确定性路由：两条条件边，各自只做一件事。

1. route_decide_or_max：确定性上限检查（不替代模型决策）。
   达到上限 -> max_iterations；未达到 -> decide。
2. route_by_next_action：只按模型决策结果 next_action 分发。
   GENERATE_SQL -> generate_sql / FIX_SQL -> fix_sql / FINALIZE -> finalize。

路由函数是纯函数：只读 State，返回下一个节点名，不产生副作用。
业务动作决策（generate / fix / finalize）由 decide 节点的 model.decide_next 决定，
路由函数不得替代模型进行业务决策。
"""

from __future__ import annotations

from examples.manual_agent_loop.types import ActionType, AgentStatus

from .state import GraphState

TERMINAL_ROUTE = "end"


def _is_terminal(state: GraphState) -> bool:
    """终止状态守卫：SUCCESS / FAILED / MAX_ITERATIONS_REACHED 不再进入下一轮。"""
    return state["status"] is not AgentStatus.RUNNING


def route_decide_or_max(state: GraphState) -> str:
    """确定性检查：终止状态 -> end；iteration >= max_iterations -> max_iterations；否则 -> decide。"""
    if _is_terminal(state):
        return TERMINAL_ROUTE
    if state["iteration"] >= state["max_iterations"]:
        return "max_iterations"
    return "decide"


def route_by_next_action(state: GraphState) -> str:
    """只按 next_action 分发；终止状态 -> end；未知动作视为 Graph Runtime 级错误。"""
    if _is_terminal(state):
        return TERMINAL_ROUTE
    if state["next_action"] is ActionType.FIX_SQL:
        return "fix_sql"
    if state["next_action"] is ActionType.FINALIZE:
        return "finalize"
    if state["next_action"] is ActionType.GENERATE_SQL:
        return "generate_sql"
    raise RuntimeError(f"unknown next_action: {state['next_action']!r}")
