## MODIFIED Requirements

### Requirement: 报告输出路径标准化

orchestrator SHALL为每次报告生成指定固定的输出路径，格式为：
```
reports/{project}_community_briefing_{YYYY-MM-DD}.html
```
其中 `{project}` 为项目名称（如 pytorch），`{YYYY-MM-DD}` 为报告生成日期。

orchestrator SHALL在调用 briefing-composer 时将完整输出路径作为参数传入。briefing-composer MUST 使用该路径写入报告文件，不得自行决定输出目录或文件名。

报告 HTML 结构 SHALL 支持以下区段（按顺序）：
1. Executive Summary
2. 高价值动态详情
3. 跨动态洞察
4. 分类动态列表
5. 数据源覆盖状态
6. 下游影响评估（Downstream Impact）— 仅当项目配置含 downstream repo
7. 报告 Diff — 可选，仅当存在前次运行结果

#### Scenario: 正常路径生成

- **WHEN** 用户执行 `pytorch` 项目的工作流，当前日期为 2026-03-23
- **THEN** orchestrator SHALL 生成输出路径 `reports/pytorch_community_briefing_2026-03-23.html` 并传递给 briefing-composer

#### Scenario: composer 遵守指定路径

- **WHEN** orchestrator 传入输出路径 `reports/pytorch_community_briefing_2026-03-23.html`
- **THEN** briefing-composer MUST 将报告写入该路径，不得写入其他目录

#### Scenario: 报告包含 Downstream Impact 区段

- **WHEN** 项目配置含 downstream repo，item-analyst 分析结果含 impact_chain 数据
- **THEN** 报告 HTML SHALL 包含 Downstream Impact 区段，位于数据源覆盖状态之后
