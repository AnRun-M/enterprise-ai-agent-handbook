"""T03 fake authoritative source（deterministic in-memory，教学规模）。

Gate A 冻结：Source of Truth 不创造业务事实——Retriever 只从权威源读取；
LLM 不得成为事实源；无结果时不得静默生成假事实。

本轮不接真实数据库 / 向量数据库 / LLM——目标是验证 contract，
不是验证基础设施。InMemoryMetadataSource 是确定性的 fake 权威源，
能表达：metadata exists / business rule exists / missing / ambiguous /
unavailable / partial（partial 由 Retriever 聚合多键结果表达，见 retrieval.py）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

CatalogKey = str


class CatalogEntryKind(Enum):
    """权威源事实的严格类型（Enum 自身拒绝未知值）。

    source-contract 边界：未知 kind 属于 programmer / authoritative-source
    contract violation（Enum 构造即 ValueError），不是 Retrieval Outcome 语义——
    "Retrieval Outcome describes authoritative lookup semantics;
    malformed source data is a contract error."
    """

    SCHEMA = "schema"
    BUSINESS_RULE = "business_rule"


@dataclass(frozen=True)
class CatalogEntry:
    """权威源中的一条事实（fake，教学规模）。

    **Runtime contract validation**（最终复审修正）：
    - kind 的类型标注（CatalogEntryKind）是静态契约；
    - `__post_init__` 在 **source boundary** 做运行时校验——
      非 CatalogEntryKind 的 kind 在构造时即 fail fast（TypeError），
      不进入 Retrieval Outcome 语义
    - 固定原则："Static type annotation ≠ runtime contract validation."
      "Malformed authoritative-source data should fail at the source
      boundary before retrieval semantics are evaluated."（畸形权威源
      数据应在 source boundary 失败，而不是进入 Retrieval Outcome 语义）
    """

    key: CatalogKey
    kind: CatalogEntryKind  # 静态标注 + 运行时校验（无 string typo 静默路径）
    content: str  # 事实内容（如 "orders: order_id, gmv_amount"）
    evidence: str  # freshness / version evidence（如 "catalog-v1" / "revision-3"）

    def __post_init__(self) -> None:
        if not isinstance(self.kind, CatalogEntryKind):
            raise TypeError("CatalogEntry.kind must be a CatalogEntryKind")


@dataclass(frozen=True)
class SourceLookup:
    """对单个 key 的权威源查询结果。

    - available=False：source operational failure（unavailable）
    - available=True 且 entries 为空：权威源明确无匹配（missing）
    - available=True 且 entries 多于一条：多个合法候选（ambiguous）
    """

    entries: tuple[CatalogEntry, ...] = field(default_factory=tuple)
    available: bool = True


class InMemoryMetadataSource:
    """确定性的 fake 权威源（教学规模）。

    构造后不可变（frozen entries / frozenset unavailable），
    lookup 只读——保证 deterministic repeated retrieval 与
    无隐藏可变全局状态。
    """

    def __init__(
        self,
        name: str,
        entries: dict[CatalogKey, tuple[CatalogEntry, ...]],
        unavailable: frozenset[CatalogKey] = frozenset(),
    ) -> None:
        self._name = name
        # 拷贝入不可变映射，防止调用方后续修改影响 source
        self._entries = {k: tuple(v) for k, v in entries.items()}
        self._unavailable = frozenset(unavailable)

    @property
    def name(self) -> str:
        return self._name

    def lookup(self, key: CatalogKey) -> SourceLookup:
        """按 key 读取事实（只读，不修改任何输入 / 状态）。"""
        if key in self._unavailable:
            return SourceLookup(entries=(), available=False)
        return SourceLookup(entries=self._entries.get(key, ()))


def build_fixture_source() -> InMemoryMetadataSource:
    """构造教学 fixture 权威源（schema facts + business rules）。

    覆盖可表达性：
    - "orders" / "gmv" 等存在（metadata / business rule exists）
    - "nonexistent_table" 缺失（missing）
    - "ambiguous_metric" 多条候选（ambiguous）
    - "broken_source" 位于 unavailable 集合（operational failure）
    """
    return InMemoryMetadataSource(
        name="catalog-v1",
        entries={
            "orders": (
                CatalogEntry(
                    key="orders",
                    kind=CatalogEntryKind.SCHEMA,
                    content="orders: order_id, gmv_amount, region, order_date",
                    evidence="catalog-v1",
                ),
            ),
            "gmv": (
                CatalogEntry(
                    key="gmv",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="GMV = 已支付订单金额合计（含税），剔除退款",
                    evidence="revision-3",
                ),
            ),
            "华东": (
                CatalogEntry(
                    key="华东",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="华东 = 上海 / 江苏 / 浙江 / 安徽 / 福建 / 江西",
                    evidence="revision-1",
                ),
            ),
            "ambiguous_metric": (
                CatalogEntry(
                    key="ambiguous_metric",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="销售额口径 A：含税订单金额",
                    evidence="revision-1",
                ),
                CatalogEntry(
                    key="ambiguous_metric",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="销售额口径 B：含税订单金额扣除退款",
                    evidence="revision-2",
                ),
            ),
        },
        unavailable=frozenset({"broken_source"}),
    )
