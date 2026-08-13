"""T03 Graph Node adapter：把 RetrievalResult 映射到 Graph State。

分层（Gate A 冻结）：
- retrieval_types.py / metadata_source.py / retrieval.py：确定性检索逻辑，
  不理解 Graph State / Graph Runtime / AgentStatus
- Node adapter（本文件）：读取检索条件 → 调用 Retriever → 返回 partial State Update

**Lifecycle 边界（本轮 Review Focus）**：
T03 的 Retrieval Outcome（complete / partial / not_found / ambiguous /
unavailable）是**业务检索结果，不是 Agent lifecycle 状态**——Node **不写**
status / failure_reason，不复制 T01 的 RUNNING → FAILED transition 规则。
检索失败（如 source unavailable）由 outcome 表达，后续如何路由
（继续 T04 / 终止 / retry / ask human）由 application control flow /
policy 决定，不由 T03 自行裁决（Gate A 冻结）。
"""

from __future__ import annotations

from .retrieval import MetadataRetriever
from .retrieval_types import RetrievalCriteria
from .state import Text2SQLState


def retrieve_metadata_node(
    state: Text2SQLState,
    retriever: MetadataRetriever,
    criteria: RetrievalCriteria,
) -> dict:
    """读检索条件 → 调 Retriever → 返回 partial State Update。

    返回：{"retrieval_result": RetrievalResult}
    - 只写 T03 自己的字段（retrieval_result）
    - 不覆盖 user_question / normalized_question / status / failure_reason
    - criteria 当前为 Proposed consumed contract（fixture）——未来由
      T02 输出产生；Integration：deferred

    依赖组装（retriever / source）在注册前由应用完成（ch18 add_node-DI 边界）。
    """
    result = retriever.retrieve(criteria)
    return {"retrieval_result": result}
