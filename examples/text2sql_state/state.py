"""Text-to-SQL State contract（Part 04，最小实现起步）。

T01 Gate A 冻结（TASK-0032）：
- user_question = 原始自然语言输入（不覆盖）
- normalized_question = 不改变业务含义的规范化自然语言输入

T03 Gate A 冻结（TASK-0033）：
- retrieval_result = T03 检索输出（outcome + references/provenance +
  materialized facts）——教学规模下小型 payload 进 State（明确的教学实现
  选择，非生产建议；生产按 architecture-map 引用策略只持久化必要引用）

T02 Gate A 冻结（TASK-0034）：
- intent_result = T02 语义解释输出（IntentResult，T02-owned derived
  state）——单个 State channel；每次正常解析整体 overwrite 旧值
  （stale semantic state 由整体替换天然避免）；T02 不写 status /
  failure_reason（semantic outcome ≠ Agent lifecycle）

最小字段集（不为单个 T 建立庞大 State abstraction）：
- 生命周期复用 manual AgentStatus（既有 lifecycle enum）
- failure 复用 status + failure_reason（不新造 normalization_error 类型）
- T03 不写 status / failure_reason（Retrieval Outcome ≠ Agent lifecycle）

教学基线（manual / basic）不修改；本包 State 随 T01-T12 演进按需扩展。
"""

from __future__ import annotations

from typing import TypedDict

from examples.manual_agent_loop.types import AgentStatus

from .retrieval_types import RetrievalResult
from .semantic_types import IntentResult


class Text2SQLState(TypedDict):
    """Part 04 图执行状态（最小契约）。

    字段语义：
    - user_question：用户原始自然语言输入（T01 不覆盖）
    - normalized_question：规范化结果（T01 写入；空输入失败时不进入后续语义解析）
    - intent_result：T02 语义解释输出（T02 写入；每次正常解析整体 overwrite；
      T02 不写 status / failure_reason）
    - retrieval_result：T03 检索输出（T03 写入；含 outcome / references /
      materialized facts——教学规模选择，非生产建议）
    - status / failure_reason：复用既有 lifecycle / failure contract
      （empty-input 是 expected application input failure，不是 Runtime exception）
    """

    user_question: str
    normalized_question: str | None
    intent_result: IntentResult | None
    retrieval_result: RetrievalResult | None
    status: AgentStatus
    failure_reason: str | None
