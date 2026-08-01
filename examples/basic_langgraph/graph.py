"""StateGraph 组装：节点注册、START、边、条件边、compile。

依赖全部通过 build_graph 参数注入，不使用隐藏全局单例。
仅使用 LangGraph Graph API（StateGraph / START / END / compile / invoke / 条件边），
不使用预构建 Agent API，不引入 LangChain。
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from examples.manual_agent_loop.models import LLM
from examples.manual_agent_loop.tools import SQLExecutor, SQLValidator

from .nodes import (
    make_finalize_node,
    make_fix_sql_node,
    make_generate_sql_node,
    make_max_iterations_node,
)
from .routing import route_after_model_action, route_start
from .state import GraphState

_ROUTE_MAP = {
    "fix_sql": "fix_sql",
    "finalize": "finalize",
    "max_iterations": "max_iterations",
}


def build_graph(
    model: LLM,
    validator: SQLValidator,
    executor: SQLExecutor,
) -> object:
    """构造并 compile 图。返回已编译图对象（LangGraph 1.2.9 的 CompiledStateGraph）。"""
    graph = StateGraph(GraphState)

    graph.add_node("generate_sql", make_generate_sql_node(model, validator))
    graph.add_node("fix_sql", make_fix_sql_node(model, validator))
    graph.add_node("finalize", make_finalize_node(executor))
    graph.add_node("max_iterations", make_max_iterations_node())

    # START -> generate_sql（条件边演示：固定首路由）
    graph.add_conditional_edges(START, route_start, {"generate_sql": "generate_sql"})
    # 生成/修复后：路由到 fix_sql / finalize / max_iterations（循环的核心条件边）
    graph.add_conditional_edges("generate_sql", route_after_model_action, _ROUTE_MAP)
    graph.add_conditional_edges("fix_sql", route_after_model_action, _ROUTE_MAP)
    # 终止：finalize 与 max_iterations 都是终点
    graph.add_edge("finalize", END)
    graph.add_edge("max_iterations", END)

    return graph.compile()
