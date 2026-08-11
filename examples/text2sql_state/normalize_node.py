"""T01 Graph Node adapter：把 pure normalization 映射到 Graph State lifecycle。

分层（Gate A 冻结）：
- pure normalization function（normalization.py）：lexical normalization，无 Runtime 逻辑
- Node adapter（本文件）：读取 State → 调用 pure function → 返回 partial State Update

Outcome contract（Gate A 冻结 + Gate B/C Review 修正）：
- empty / whitespace-only = expected application input failure ≠ Runtime exception
- 复用 status + failure_reason（AgentStatus），不新造 normalization_error 类型
- 不抛业务异常
- **T01 Node 对 normalized_question / status / failure_reason 形成完整
  outcome update**（两者都不覆盖 user_question）：
  - success 清理 stale failure state（写 RUNNING + failure_reason=None）
  - failure 清理 stale normalized value（写 normalized_question=None）
  - 理由：merge 语义下"不返回字段" = "保留已有字段值"；T01 Node 对自己
    拥有的 outcome / derived fields 必须使上一 outcome 的 stale 值失效
"""

from __future__ import annotations

from examples.manual_agent_loop.types import AgentStatus

from .normalization import normalize_question
from .state import Text2SQLState

_INVALID_INPUT_REASON = "empty question: no valid input after normalization"


def normalize_input_node(state: Text2SQLState) -> dict:
    """读 user_question → 规范化 → 返回部分 State Update。

    outcome update（三字段完整表达，值表达不同 outcome；不覆盖 user_question）：

    success（valid input）：
        {"normalized_question": <normalized>,
         "status": AgentStatus.RUNNING,
         "failure_reason": None}
        （success 清理 stale failure state——旧 FAILED / failure_reason
        在 merge 下不显式清空会残留）

    failure（empty / whitespace-only）：
        {"normalized_question": None,
         "status": AgentStatus.FAILED,
         "failure_reason": <reason>}
        （failure 显式 invalidates derived normalized_question，
        防止旧派生值在 State merge 后残留）
    """
    normalized = normalize_question(state["user_question"])
    if normalized is None:
        return {
            "normalized_question": None,
            "status": AgentStatus.FAILED,
            "failure_reason": _INVALID_INPUT_REASON,
        }
    return {
        "normalized_question": normalized,
        "status": AgentStatus.RUNNING,
        "failure_reason": None,
    }
