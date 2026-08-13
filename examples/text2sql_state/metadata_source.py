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

    **Identity 模型**（Task Merge Gate Review 修正）：
    - `entry_id` = **稳定 source-local fact identity**（"这条事实是谁"）；
      `key` = **retrieval / semantic lookup key**；`evidence` = **freshness
      / version evidence**
    - 固定原则："Fact identity ≠ freshness/version evidence."
      （事实身份不等于版本 / 新鲜度证据——同一事实的 evidence 更新
      不代表 identity 变化；同一 key / 同一 evidence 下不同内容也不是
      同一事实）

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

    entry_id: str  # 稳定 source-local fact identity（deterministic / 可读 / 不依赖 object identity）
    key: CatalogKey  # retrieval / semantic lookup key（index 身份校验，见 InMemoryMetadataSource）
    kind: CatalogEntryKind  # 静态标注 + 运行时校验（无 string typo 静默路径）
    content: str  # 事实内容（如 "orders: order_id, gmv_amount"）
    evidence: str  # freshness / version evidence（如 "catalog-v1" / "revision-3"）——不是 identity

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
    """确定性的 fake 权威源（read-only source snapshot，教学规模）。

    **Source identity validation**（最终复审修正）：
    - 构造阶段校验每个 index_key 下的 `CatalogEntry.key == index_key`——
      mismatch 会造成 silent provenance corruption（lookup("orders") 却
      产出 `source_ref=catalog:customers`），构造即 fail fast，
      不进入 lookup / Retriever / Retrieval Outcome
    - 固定原则："Source index identity must agree with entry identity."
      "Provenance correctness starts at source construction,
      not at retrieval output formatting."（权威源索引键与事实条目标识
      必须一致；provenance 的正确性从 source construction 开始，
      而不是在 Retriever 输出时修补）

    **Fact identity uniqueness invariant**（Task Merge Gate Review 修正）：
    - 同一个 source snapshot 内 `entry_id` 必须**全局唯一**（跨所有
      index key）——否则 Retriever 会产生 duplicate fact_id，provenance
      binding 无法解析；唯一性在 **source construction 即 fail fast**，
      不等到 Retriever 输出时才发现
    - 固定原则："Fact identity uniqueness is a source-boundary invariant."
      （事实身份唯一性是 source-boundary 不变量——合法 source 构造后，
      entry_id 即承担稳定 fact identity，key 只承担 lookup 职责）

    **Snapshot semantics**：构造时复制调用方 entries 为 read-only
    source snapshot——公开 API 仅暴露只读 lookup；调用方后续修改原始
    输入容器不会改变 source snapshot。**不声称 Python 对象绝对
    immutable**（内部为私有 dict 拷贝），保证 deterministic repeated
    retrieval 与无隐藏可变全局状态。
    """

    def __init__(
        self,
        name: str,
        entries: dict[CatalogKey, tuple[CatalogEntry, ...]],
        unavailable: frozenset[CatalogKey] = frozenset(),
    ) -> None:
        self._name = name
        # 1) index / entry identity validation：mismatch 构造即失败
        for index_key, values in entries.items():
            for entry in values:
                if entry.key != index_key:
                    raise ValueError(
                        "CatalogEntry.key must match source index key: "
                        f"index={index_key!r}, entry.key={entry.key!r}"
                    )
        # 2) fact identity uniqueness：同一个 source snapshot 内 entry_id 全局唯一
        #    （跨所有 index key）——重复 entry_id 会产生 duplicate fact_id，
        #    provenance binding 无法解析；构造即 fail fast
        seen_entry_ids: set[str] = set()
        for index_key, values in entries.items():
            for entry in values:
                if entry.entry_id in seen_entry_ids:
                    raise ValueError(
                        "CatalogEntry.entry_id must be unique within a source "
                        f"snapshot: duplicate entry_id={entry.entry_id!r} "
                        f"(at index {index_key!r})"
                    )
                seen_entry_ids.add(entry.entry_id)
        # 3) 拷贝为 read-only snapshot（调用方后续修改原始容器不影响 source）
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

    entry_id 命名（稳定 fact identity，与 evidence 无关）：
    schema.orders / metric.gmv / region.east_china /
    metric.sales_definition.a / metric.sales_definition.b——
    deterministic / 可读 / 不依赖 object identity / 不依赖随机 UUID /
    不依赖 criteria 顺序 / 不把 evidence 当 identity。
    """
    return InMemoryMetadataSource(
        name="catalog-v1",
        entries={
            "orders": (
                CatalogEntry(
                    entry_id="schema.orders",
                    key="orders",
                    kind=CatalogEntryKind.SCHEMA,
                    content="orders: order_id, gmv_amount, region, order_date",
                    evidence="catalog-v1",
                ),
            ),
            "gmv": (
                CatalogEntry(
                    entry_id="metric.gmv",
                    key="gmv",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="GMV = 已支付订单金额合计（含税），剔除退款",
                    evidence="revision-3",
                ),
            ),
            "华东": (
                CatalogEntry(
                    entry_id="region.east_china",
                    key="华东",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="华东 = 上海 / 江苏 / 浙江 / 安徽 / 福建 / 江西",
                    evidence="revision-1",
                ),
            ),
            "ambiguous_metric": (
                CatalogEntry(
                    entry_id="metric.sales_definition.a",
                    key="ambiguous_metric",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="销售额口径 A：含税订单金额",
                    evidence="revision-1",
                ),
                CatalogEntry(
                    entry_id="metric.sales_definition.b",
                    key="ambiguous_metric",
                    kind=CatalogEntryKind.BUSINESS_RULE,
                    content="销售额口径 B：含税订单金额扣除退款",
                    evidence="revision-2",
                ),
            ),
        },
        unavailable=frozenset({"broken_source"}),
    )
