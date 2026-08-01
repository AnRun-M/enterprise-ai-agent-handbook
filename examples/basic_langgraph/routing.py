"""确定性路由：把 manual_agent_loop 的 decide_next + 循环条件翻译为条件边。

路由函数是纯函数：只读 State，返回下一个节点名，不产生副作用。
"""

from __future__ import annotations

from .state import GraphState


def route_start(state: GraphState) -> str:
    """START 的固定入口：首轮总是生成 SQL。"""
    return "generate_sql"


def route_after_model_action(state: GraphState) -> str:
    """等价于手写 Runtime 的「进入下一节点前检查」+ decide_next。

    顺序与手写版本完全一致：
    1. 迭代上限检查优先——达到上限即使校验通过也终止（finalize 不会执行）；
    2. 校验失败 -> fix_sql；
    3. 校验通过 -> finalize。
    """
    if state["iteration"] >= state["max_iterations"]:
        return "max_iterations"
    if state["validation_error"] is not None:
        return "fix_sql"
    return "finalize"
