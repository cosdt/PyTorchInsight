## ADDED Requirements

### Requirement: 报告输出路径标准化

orchestrator SHALL为每次报告生成指定固定的输出路径，格式为：
```
reports/{project}_community_briefing_{YYYY-MM-DD}.html
```
其中 `{project}` 为项目名称（如 pytorch），`{YYYY-MM-DD}` 为报告生成日期。

orchestrator SHALL在调用 briefing-composer 时将完整输出路径作为参数传入。briefing-composer MUST 使用该路径写入报告文件，不得自行决定输出目录或文件名。

#### Scenario: 正常路径生成

- **WHEN** 用户执行 `pytorch` 项目的工作流，当前日期为 2026-03-17
- **THEN** orchestrator SHALL 生成输出路径 `reports/pytorch_community_briefing_2026-03-17.html` 并传递给 briefing-composer

#### Scenario: composer 遵守指定路径

- **WHEN** orchestrator 传入输出路径 `reports/pytorch_community_briefing_2026-03-17.html`
- **THEN** briefing-composer MUST 将报告写入该路径，不得写入 `output/` 或其他目录

### Requirement: 报告文件防覆盖

当指定输出路径已存在同名文件时，orchestrator SHALL 在文件名中追加序号后缀以避免覆盖：
```
reports/{project}_community_briefing_{YYYY-MM-DD}_v2.html
```

#### Scenario: 同日多次运行

- **WHEN** `reports/pytorch_community_briefing_2026-03-17.html` 已存在
- **THEN** orchestrator SHALL 将输出路径调整为 `reports/pytorch_community_briefing_2026-03-17_v2.html`

#### Scenario: 多次重复运行

- **WHEN** `_v2.html` 也已存在
- **THEN** orchestrator SHALL 递增序号为 `_v3.html`
