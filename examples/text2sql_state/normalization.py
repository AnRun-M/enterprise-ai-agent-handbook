"""T01 输入规范化：deterministic lexical normalization（canonical T01）。

Gate A 冻结边界（TASK-0032）：
- 只做：trim、whitespace canonicalization、empty-input detection、
  不改变业务含义的 lexical normalization
- 不做：semantic rewriting（metric / dimension / entity / time range /
  filters / intent facts 抽取——属于 T02）、同义词改写、指标名映射、
  拼写智能纠正、LLM rewrite、lowercase 全文、删除标点、重排词序

原则："Normalize representation, not meaning."

idempotency 为 application contract / engineering property：
normalize(normalize(x)) 观察等价 normalize(x)。
"""

from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")


def normalize_question(question: str) -> str | None:
    """规范化用户问题（纯函数，无副作用）。

    返回：
    - 规范化后的字符串（trim + 连续空白折叠为单个空格；不做语义改写）
    - None 表示 invalid input（empty / whitespace-only）——显式失败标记，
      调用方据此走 existing lifecycle / failure contract，而非抛业务异常。
    """
    normalized = _WS_RE.sub(" ", question.strip())
    if not normalized:
        return None
    return normalized
