"""StateGraph 组装：节点注册、START、边、条件边、compile。

依赖全部通过 build_graph 参数注入，不使用隐藏全局单例。
仅使用 LangGraph Graph API（StateGraph / START / END / compile / invoke / 条件边），
不使用预构建 Agent API，不引入 LangChain。

图结构（对应手写 Agent Loop）：
    START -> [route_decide_or_max] -> decide | max_iterations
    decide -> [route_by_next_action] -> generate_sql | fix_sql | finalize
    generate_sql / fix_sql -> [route_decide_or_max] -> decide | max_iterations（循环回路）
    finalize -> END / max_iterations -> END（终止）
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from examples.manual_agent_loop.models import LLM
from examples.manual_agent_loop.tools import SQLExecutor, SQLValidator

from .nodes import (
    make_decide_node,
    make_finalize_node,
    make_fix_sql_node,
    make_generate_sql_node,
    make_max_iterations_node,
)
from .routing import TERMINAL_ROUTE, route_by_next_action, route_decide_or_max
from .state import GraphState

_DECIDE_OR_MAX_MAP = {
    "decide": "decide",
    "max_iterations": "max_iterations",
    TERMINAL_ROUTE: END,
}
_BY_ACTION_MAP = {
    "generate_sql": "generate_sql",
    "fix_sql": "fix_sql",
    "finalize": "finalize",
    TERMINAL_ROUTE: END,
}


def build_graph(
    model: LLM,
    validator: SQLValidator,
    executor: SQLExecutor,
) -> object:
    """构造并 compile 图。返回已编译图对象（LangGraph 1.2.9 的 CompiledStateGraph）。"""
    graph = StateGraph(GraphState)

    graph.add_node("decide", make_decide_node(model))
    graph.add_node("generate_sql", make_generate_sql_node(model, validator))
    graph.add_node("fix_sql", make_fix_sql_node(model, validator))
    graph.add_node("finalize", make_finalize_node(executor))
    graph.add_node("max_iterations", make_max_iterations_node())

    # 入口与循环回路：确定性上限检查 -> decide（业务决策）或 max_iterations（兜底终止）
    graph.add_conditional_edges(START, route_decide_or_max, _DECIDE_OR_MAX_MAP)
    graph.add_conditional_edges("generate_sql", route_decide_or_max, _DECIDE_OR_MAX_MAP)
    graph.add_conditional_edges("fix_sql", route_decide_or_max, _DECIDE_OR_MAX_MAP)
    # 模型决策分发：只按 next_action 路由
    graph.add_conditional_edges("decide", route_by_next_action, _BY_ACTION_MAP)
    # 终止
    graph.add_edge("finalize", END)
    graph.add_edge("max_iterations", END)

    return graph.compile()
