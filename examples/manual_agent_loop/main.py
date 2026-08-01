"""最小启动入口：运行一次「查询昨天的 GMV」，打印每轮状态与最终结果。

运行方式（仓库根目录）：

    python -m examples.manual_agent_loop.main
"""

from __future__ import annotations

import sys

from .agent import Agent
from .config import AgentConfig
from .state import AgentState
from .types import AgentStatus


def render(state: AgentState) -> str:
    lines = [f"== 用户问题：{state.user_question} =="]
    for event in state.history:
        action = event.action.value if event.action else "-"
        lines.append(
            f"  第 {event.iteration} 轮 | 动作={action} | 状态={event.status.value}"
            f" | 校验错误={event.validation_error or '-'}"
        )
        if event.sql:
            lines.append(f"    SQL: {event.sql}")
    lines.append(f"== 最终状态：{state.status.value} ==")
    if state.final_answer is not None:
        lines.append(f"== 最终回答：{state.final_answer} ==")
    elif state.status is AgentStatus.MAX_ITERATIONS_REACHED:
        lines.append(f"== 达到最大迭代次数（{state.max_iterations}）后安全终止 ==")
    elif state.status is AgentStatus.FAILED:
        lines.append(f"== 任务失败：{state.failure_reason or 'unknown'} ==")
    return "\n".join(lines)


def main() -> None:
    # Windows 控制台默认 GBK 无法输出 ¥（U+00A5），显式使用 UTF-8 输出。
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    config = AgentConfig()
    agent = Agent(config=config)
    state = agent.invoke("查询昨天的 GMV")
    print(render(state))


if __name__ == "__main__":
    main()
