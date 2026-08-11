"""T01 Graph Node adapter：把 pure normalization 映射到 Graph State lifecycle。

分层（Gate A 冻结）：
- pure normalization function（normalization.py）：lexical normalization，无 Runtime 逻辑
- Node adapter（本文件）：读取 State → 调用 pure function → 返回 partial State Update

Failure contract（Gate A 冻结 + Review 修正）：
- empty / whitespace-only = expected application input failure ≠ Runtime exception
- 复用 status + failure_reason（AgentStatus），不新造 normalization_error 类型
- 不抛业务异常

Field ownership + transition authority（Task Merge Gate Review 最终冻结）：
- normalized_question = **T01-owned derived field**——T01 始终拥有其派生值生命周期
- status / failure_reason = **shared lifecycle fields**——T01 只拥有
  invalid input 导致的 **RUNNING → FAILED** 这一个状态迁移，
  不拥有这些字段的完整生命周期
- 原则："Field write capability ≠ field ownership."
- 进一步："Shared field ownership can be transition-scoped,
  not field-wide."（共享字段的写权限可以只属于某个明确状态迁移，
  而不是拥有整个字段生命周期）
"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus

from .normalization import normalize_question
from .state import Text2SQLState

_INVALID_INPUT_REASON = "empty question: no valid input after normalization"


def normalize_input_node(state: Text2SQLState) -> dict:
    """读 user_question → 规范化 → 返回部分 State Update。

    field ownership 两层 + transition authority：
    - normalized_question = T01-owned derived field（始终由 T01 管理）
    - status / failure_reason = shared lifecycle fields（T01 仅拥有
      RUNNING + invalid input → FAILED 这一个状态迁移）

    success（valid input）：
        {"normalized_question": <normalized>}
        （不覆盖 user_question；不触碰 shared lifecycle）

    failure（empty / whitespace-only）：
        始终 {"normalized_question": None}（T01-owned 必须 invalidates stale 值）；
        仅当 state["status"] is RUNNING 时追加
        {"status": FAILED, "failure_reason": T01 reason}——
        已处于其它 lifecycle outcome（FAILED / SUCCESS /
        MAX_ITERATIONS_REACHED）时不得覆盖 shared lifecycle：
        不得替换已有 failure cause、不得把终止状态改成 FAILED。
    """
    normalized = normalize_question(state["user_question"])
    if normalized is not None:
        return {"normalized_question": normalized}

    update = {"normalized_question": None}
    if state["status"] is AgentStatus.RUNNING:
        update.update(
            status=AgentStatus.FAILED,
            failure_reason=_INVALID_INPUT_REASON,
        )
    return update
