# Changelog

## [Unreleased]

### Added

- `.ai/context` 项目记忆
- `.ai/tasks` 任务目录
- `.ai/templates` 模板目录
- ADR 目录
- MkDocs 配置
- 章节、示例和测试骨架
- AI-Native 仓库结构
- ADR-0003 ~ ADR-0006 独立 ADR 文件
- Text-to-SQL canonical 流程（`docs/04-text2sql/canonical-pipeline.md`）
- 章节—示例—测试映射（`docs/00-introduction/content-map.md`）

### Changed

- ADR 唯一事实源收敛至 `docs/adr/`，`decisions.md` 降级为索引
- AI 协作规则收敛至 `AGENTS.md`，按影响范围更新
- 示例目录改为可标准导入的 Python 包命名（去数字前缀、下划线，含 `__init__.py`）
- 章节文件改为 `chXX-` 命名，Part 01 补充 index
- 删除 `diagrams/`，Mermaid 图随章节内联
- v0.2.0 里程碑尚未完成，从已发布移入 Unreleased
