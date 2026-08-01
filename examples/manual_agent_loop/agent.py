"""组合层：组装依赖（依赖注入），对外提供 invoke()。"""

from __future__ import annotations

from .config import AgentConfig
from .models import LLM, FakeLLM
from .runtime import AgentRuntime
from .state import AgentState
from .tools import FakeSQLExecutor, FakeSQLValidator, SQLExecutor, SQLValidator


class Agent:
    """最小 Agent：接收用户问题，返回完整执行状态。

    默认注入确定性 Fake 组件；真实 LLM / 执行引擎可通过构造参数替换（依赖注入）。
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        model: LLM | None = None,
        validator: SQLValidator | None = None,
        executor: SQLExecutor | None = None,
    ) -> None:
        self._config = config or AgentConfig()
        self._runtime = AgentRuntime(
            model=model or FakeLLM(self._config),
            validator=validator or FakeSQLValidator(self._config),
            executor=executor or FakeSQLExecutor(),
        )

    def invoke(self, user_question: str) -> AgentState:
        state = AgentState(user_question=user_question, max_iterations=self._config.max_iterations)
        return self._runtime.run(state)
