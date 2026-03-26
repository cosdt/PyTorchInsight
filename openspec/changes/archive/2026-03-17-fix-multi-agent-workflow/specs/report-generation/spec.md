## MODIFIED Requirements

### Requirement: 报告内容组织

`briefing-composer` SHALL将分析结果组织为以下报告结构：
1. **Executive Summary**: 时间窗口内的关键发现概览（3-5个要点）。Executive Summary中MUST引用至少一条GitHub来源的动态（如果coordinator返回的数据中包含GitHub条目）
2. **高价值动态详情**: 按影响等级排序的深度分析结果，每条包含evidence_sources引用
3. **跨动态洞察**: 从wisdom notepad提炼的跨动态模式（如"本周distributed training模块有密集重构活动"）
4. **分类动态列表**: 按类型（PR/Issue/RFC/Discussion）分类的**完整**动态列表。composer MUST包含coordinator返回的所有分类条目，不得自行筛选或裁剪。GitHub来源的条目MUST在PR和Issue类别中明确呈现
5. **数据源覆盖状态**: 各数据源的采集情况、降级标记和失败项说明。MUST包含coordinator提供的数据统计信息（采集数、融合后数、呈现数）

#### Scenario: 报告结构完整

- **WHEN** briefing-composer接收到包含5条高价值分析、20条普通动态和wisdom总结的数据
- **THEN** 生成的报告SHALL包含executive summary、5条详细分析（含evidence引用）、跨动态洞察、按类型分类的20条动态列表（全部呈现，不裁剪）、数据源状态

#### Scenario: 降级数据源标注

- **WHEN** github-scout通过gh CLI降级获取了数据
- **THEN** 报告的数据源覆盖状态SHALL标注"GitHub: 降级模式（gh CLI），数据可能不完整"

#### Scenario: GitHub数据在报告中体现

- **WHEN** coordinator返回的分类动态列表中包含15条GitHub PR和8条GitHub Issue
- **THEN** 报告的分类动态列表中MUST包含这15条PR和8条Issue，不得因偏好Blog/Discourse来源而省略

#### Scenario: 数据统计在报告中展示

- **WHEN** coordinator返回的数据统计显示"采集120条 → 融合后95条 → 高价值分析5条"
- **THEN** 报告的数据源覆盖状态部分MUST展示这些统计数字，帮助用户了解数据管道的信息保留情况
