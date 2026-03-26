## MODIFIED Requirements

### Requirement: 报告输出路径标准化

orchestrator SHALL为每次报告生成指定固定的输出路径，格式为：
```
reports/{project}_community_briefing_{YYYY-MM-DD}.md
```
其中 `{project}` 为项目名称（如 pytorch），`{YYYY-MM-DD}` 为报告生成日期。

orchestrator SHALL在调用 briefing-composer 时将完整输出路径作为参数传入。briefing-composer MUST 使用该路径写入报告文件，不得自行决定输出目录或文件名。

#### Scenario: 正常路径生成

- **WHEN** 用户执行 `pytorch` 项目的工作流，当前日期为 2026-03-17
- **THEN** orchestrator SHALL 生成输出路径 `reports/pytorch_community_briefing_2026-03-17.md` 并传递给 briefing-composer

#### Scenario: composer 遵守指定路径

- **WHEN** orchestrator 传入输出路径 `reports/pytorch_community_briefing_2026-03-17.md`
- **THEN** briefing-composer MUST 将报告写入该路径，不得写入 `output/` 或其他目录

### Requirement: 报告文件防覆盖

当指定输出路径已存在同名文件时，orchestrator SHALL 在文件名中追加序号后缀以避免覆盖：
```
reports/{project}_community_briefing_{YYYY-MM-DD}_v2.md
```

#### Scenario: 同日多次运行

- **WHEN** `reports/pytorch_community_briefing_2026-03-17.md` 已存在
- **THEN** orchestrator SHALL 将输出路径调整为 `reports/pytorch_community_briefing_2026-03-17_v2.md`

#### Scenario: 多次重复运行

- **WHEN** `_v2.md` 也已存在
- **THEN** orchestrator SHALL 递增序号为 `_v3.md`

### Requirement: Markdown 区段结构

报告 Markdown SHALL 按以下顺序包含区段（使用 `##` 二级标题）：

1. **Executive Summary** — 必需
2. **高价值动态详情** — 必需
3. **跨动态洞察** — 必需
4. **分类动态列表** — 必需
5. **数据源覆盖状态** — 必需
6. **下游影响评估（Downstream Impact）** — 条件（仅当 project_config 包含 `role: downstream` 仓库且存在 impact_chain 数据时）
7. **报告 Diff** — 可选（仅当同项目存在前次报告时）

#### Scenario: 完整区段结构（含下游影响）

- **WHEN** project_config 中存在 downstream 仓库且 item-analyst 返回了 impact_chain 数据
- **THEN** 报告 Markdown SHALL 包含 7 个区段，每个区段以 `##` 标题开头，按上述顺序排列

#### Scenario: 基础区段结构（无下游影响）

- **WHEN** project_config 中不存在 downstream 仓库
- **THEN** 报告 Markdown SHALL 包含 5 个必需区段，不包含 Downstream Impact 和 Report Diff
