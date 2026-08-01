"""最小启动入口：运行 LangGraph 版「查询昨天的 GMV」。

输出格式与 manual_agent_loop.main 保持一致，便于读者逐轮对照。

运行方式（仓库根目录）：

    python -m examples.basic_langgraph.main
"""

from __future__ import annotations

import sys

from examples.manual_agent_loop.config import AgentConfig
from examples.manual_agent_loop.types import AgentStatus

from .agent import LangGraphAgent
from .state import GraphState


def render(state: GraphState) -> str:
    lines = [f"== 用户问题：{state['user_question']} =="]
    for event in state["history"]:
        action = event.action.value if event.action else "-"
        lines.append(
            f"  第 {event.iteration} 轮 | 动作={action} | 状态={event.status.value}"
            f" | 校验错误={event.validation_error or '-'}"
        )
        if event.sql:
            lines.append(f"    SQL: {event.sql}")
    lines.append(f"== 最终状态：{state['status'].value} ==")
    if state["final_answer"] is not None:
        lines.append(f"== 最终回答：{state['final_answer']} ==")
    elif state["status"] is AgentStatus.MAX_ITERATIONS_REACHED:
        lines.append(f"== 达到最大迭代次数（{state['max_iterations']}）后安全终止 ==")
    elif state["status"] is AgentStatus.FAILED:
        lines.append(f"== 任务失败：{state['failure_reason'] or 'unknown'} ==")
    return "\n".join(lines)


def main() -> None:
    # Windows 控制台默认 GBK 无法输出 ¥（U+00A5），显式使用 UTF-8 输出。
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    agent = LangGraphAgent(config=AgentConfig())
    state = agent.invoke("查询昨天的 GMV")
    print(render(state))


if __name__ == "__main__":
    main()
