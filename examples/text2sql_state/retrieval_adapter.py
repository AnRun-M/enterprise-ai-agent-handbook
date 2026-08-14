"""T02 → T03 source-specific adapter（三层接口的最后一层）。

Gate A 冻结（TASK-0034 十三节 方案 2，固定原则）：
    "Semantic interpretation ≠ retrieval requirement ≠ source-specific
    retrieval criteria."

    IntentResult（semantic interpretation）
        ↓
    source-agnostic retrieval requirements（逻辑契约层，不绑定 source vocabulary）
        ↓
    integration / source-specific adapter（本文件）
        ↓
    T03 RetrievalCriteria（Proposed fixture / source-specific query representation）

- **RetrievalCriteria 继续保持 T03 fixture 身份**，不升级为 T02 final
  semantic contract；fake source key vocabulary 只存在于本 adapter，
  **不得进入 IntentResult**（Gate A 禁止事项）
- adapter 是 source-specific 层，可独立单测；T02 Node 不调用本 adapter
  （"Having retrieval requirements does not authorize T02 to invoke T03."）
- **空 requirements → 返回 None**：UNSUPPORTED 等结果没有可映射的检索需求，
  adapter 绝不为其自动生成普通 RetrievalCriteria；T03 对空 criteria 视为
  consumed-contract violation，返回 None 表示"无需检索"，由集成层决定
  不调用 T03（"outcome = UNSUPPORTED 却自动生成普通 RetrievalCriteria"
  在结构上不可表达）
- 未映射的 semantic ref / category → ValueError：source vocabulary 缺口是
  integration gap，必须显式设计，不得静默跳过（fail-fast at adapter
  boundary，与 T03 的 source-boundary 校验哲学一致）
"""

from __future__ import annotations

from .retrieval_types import RetrievalCriteria
from .semantic_types import RetrievalPurpose, RetrievalRequirement, SemanticCategory

_VERIFY_DEFINITION_KEYS: dict[str, str] = {
    "GMV": "gmv",
    "订单数": "orders",
    "华东": "华东",
    "华南": "region.south_china",
    "已支付": "status.paid",
    "未支付": "status.unpaid",
    "VIP用户": "segment.vip",
    "VIP": "segment.vip",
    "区域": "dimension.region",
    "日期": "dimension.date",
}

_RESOLVE_AMBIGUITY_KEYS: dict[SemanticCategory, str] = {
    SemanticCategory.METRIC: "ambiguous_metric",
}

_COMPLETE_INTERPRETATION_KEYS: dict[SemanticCategory, str] = {
    SemanticCategory.TIME_RANGE: "business_calendar",
}


def build_retrieval_criteria(
    requirements: tuple[RetrievalRequirement, ...],
) -> RetrievalCriteria | None:
    """把 source-agnostic retrieval requirements 映射为 T03 RetrievalCriteria。

    - 空 requirements → None（无检索需求；UNSUPPORTED 不会得到普通 criteria）
    - 每个 requirement 按 purpose + semantic_ref / category 映射到 fake
      source lookup key；去重 + 排序保证确定性（criteria 排列顺序无业务
      语义——T03 以排列无关方式消费）
    - 未映射 ref / category → ValueError（integration gap，fail-fast）

    Returns:
        RetrievalCriteria | None：None 表示没有可映射的检索需求（无需检索）。
    """
    if not requirements:
        return None
    keys: list[str] = []
    for requirement in requirements:
        if requirement.purpose is RetrievalPurpose.VERIFY_DEFINITION:
            key = _VERIFY_DEFINITION_KEYS.get(requirement.semantic_ref)
            if key is None:
                raise ValueError(
                    "no source key vocabulary for semantic ref "
                    f"{requirement.semantic_ref!r} (VERIFY_DEFINITION)"
                )
        elif requirement.purpose is RetrievalPurpose.RESOLVE_AMBIGUITY:
            key = _RESOLVE_AMBIGUITY_KEYS.get(requirement.category)
            if key is None:
                raise ValueError(
                    "no source key vocabulary for ambiguity resolution of "
                    f"category {requirement.category.value}"
                )
        elif requirement.purpose is RetrievalPurpose.COMPLETE_INTERPRETATION:
            key = _COMPLETE_INTERPRETATION_KEYS.get(requirement.category)
            if key is None:
                raise ValueError(
                    "no source key vocabulary for completing interpretation of "
                    f"category {requirement.category.value}"
                )
        else:
            # Enum 已封顶；防御性 impossible-branch protection——
            # 未知 purpose 是 contract error，不是合法映射路径
            raise ValueError(f"unknown retrieval purpose: {requirement.purpose}")
        keys.append(key)
    return RetrievalCriteria(keys=tuple(sorted(set(keys))))
