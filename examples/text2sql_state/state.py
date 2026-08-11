"""Text-to-SQL State contract（Part 04，最小实现起步）。

T01 Gate A 冻结（TASK-0032）：
- user_question = 原始自然语言输入（不覆盖）
- normalized_question = 不改变业务含义的规范化自然语言输入

最小字段集（不为 T01 建立庞大 State abstraction）：
- 生命周期复用 manual AgentStatus（既有 lifecycle enum）
- failure 复用 status + failure_reason（不新造 normalization_error 类型）

教学基线（manual / basic）不修改；本包 State 随 T01-T12 演进按需扩展。
"""

from __future__ import annotations

from typing import TypedDict

from examples.manual_agent_loop.types import AgentStatus


class Text2SQLState(TypedDict):
    """Part 04 图执行状态（最小契约）。

    字段语义：
    - user_question：用户原始自然语言输入（T01 不覆盖）
    - normalized_question：规范化结果（T01 写入；空输入失败时不进入后续语义解析）
    - status / failure_reason：复用既有 lifecycle / failure contract
      （empty-input 是 expected application input failure，不是 Runtime exception）
    """

    user_question: str
    normalized_question: str | None
    status: AgentStatus
    failure_reason: str | None
