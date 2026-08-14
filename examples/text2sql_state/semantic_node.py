"""T02 Graph Node adapter：把 IntentResult 映射到 Graph State。

分层（Gate A 冻结）：
- semantic_types.py / semantic_parser.py：纯语义解释逻辑，不理解
  Graph State / Graph Runtime / AgentStatus
- Node adapter（本文件）：读取 normalized_question → 调用 parser →
  返回 partial State Update

**Lifecycle / routing 边界（Gate A 十九节 第 9 项冻结）**：
- T02 的 semantic outcome（COMPLETE / PARTIAL / AMBIGUOUS / UNSUPPORTED）
  是**业务语义结果，不是 Agent lifecycle 状态**——Node **不写**
  status / failure_reason，不复制 T01 的 RUNNING → FAILED transition 规则
- T02 **不调用 / route / retry T03**、不 clarification routing、不 terminate
  graph——"Retrieval requirement is data, not routing."；路由 / 澄清 / 终止
  由 application control flow / Node / Edge / Command / Runtime 表达
- **每次正常解析都返回完整新 IntentResult** → 默认 overwrite 语义下整体替换
  上一轮 intent_result（stale semantic state 由整体替换天然避免，方案 C 优势）

**failure-boundary 决策（Gate B）**：
- consumed-contract violation（normalized_question 为 None）→ **ValueError**，
  不进入 outcome taxonomy（invalid consumed input ≠ semantic outcome）；
  pure parser 接收 str，Node adapter 保证输入契约
- 违约路径抛异常 → 无 State update；Node **不写 intent_result=None**：
  T01 失败（normalized_question=None）时 lifecycle 已由 T01 的
  RUNNING → FAILED transition 处理；合法输入路径永远整体 overwrite
  intent_result——"None means no valid T02 semantic result exists; it is
  not the representation of UNSUPPORTED."（本 Gate B 版本中 None 路径不
  由 T02 Node 写入，四种 expected outcome 都返回完整 IntentResult）
"""

from __future__ import annotations

from .semantic_parser import SemanticParser
from .state import Text2SQLState


def parse_intent_node(state: Text2SQLState, parser: SemanticParser) -> dict:
    """读 normalized_question → 调 parser → 返回 partial State Update。

    Node 依赖 **SemanticParser 语义契约**（Protocol），不依赖 FakeSemanticParser
    fake implementation——FakeSemanticParser 是当前注入的 implementation，
    未来真实 LLM parser 只要实现 `parse(str) -> IntentResult` 即可替换
    （ch18 add_node-DI 边界）。

    返回：{"intent_result": IntentResult}
    - 只写 T02-owned derived field（intent_result）
    - 不覆盖 user_question / normalized_question / status / failure_reason
    - 不调用 / 路由 T03（本函数签名无 retriever / criteria 依赖）
    - parser 依赖组装（注入）在注册前由应用完成（ch18 add_node-DI 边界）

    Raises:
        ValueError: normalized_question 为 None（consumed-contract violation）。
    """
    normalized = state["normalized_question"]
    if normalized is None:
        raise ValueError(
            "normalized_question is None: T02 expects T01 output "
            "(consumed-contract violation)"
        )
    return {"intent_result": parser.parse(normalized)}
