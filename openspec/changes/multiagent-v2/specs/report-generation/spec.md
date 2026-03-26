## MODIFIED Requirements

### Requirement: 报告内容组织

`briefing-composer` SHALL将分析结果组织为以下报告结构：
1. **Executive Summary**: 时间窗口内的关键发现概览（3-5个要点）。Executive Summary中MUST引用至少一条GitHub来源的动态（如果coordinator返回的数据中包含GitHub条目）
2. **高价值动态详情**: 按影响等级排序的深度分析结果，每条包含evidence_sources引用
3. **跨动态洞察**: 从wisdom notepad提炼的跨动态模式
4. **分类动态列表**: 按类型分类的**完整**动态列表。composer MUST包含coordinator返回的所有分类条目，不得自行筛选或裁剪
5. **数据源覆盖状态**: 各数据源的采集情况、降级标记和失败项说明
6. **下游影响评估（Downstream Impact）**（仅当项目配置含 downstream repo 时）: 按风险等级分组呈现所有具有 cross-project 影响的高价值项
7. **报告 Diff**（可选，仅当存在前次运行结果时）: 新增/升级/已解决的 item 对比

Composer SHALL 从 staging 目录读取数据（coordinator_result.md、phase3_item_*.md、wisdom.md），而非从 orchestrator 对话消息获取。

#### Scenario: 报告结构完整（含新增区段）

- **WHEN** briefing-composer 读取 staging 目录中的分析结果，项目配置含 downstream repo
- **THEN** 生成的报告 SHALL 包含 7 个区段（含 Downstream Impact），Downstream Impact 区段按风险等级分组

#### Scenario: 无 downstream repo 时 6 个区段

- **WHEN** 项目配置不含 downstream repo
- **THEN** 报告 SHALL 包含原 5 个区段，不包含 Downstream Impact 区段

#### Scenario: Composer 从 staging 读取数据

- **WHEN** orchestrator 调用 composer 并传入 staging 目录路径
- **THEN** composer SHALL 读取 staging 目录中的 coordinator_result.md、phase3_item_*.md、wisdom.md 等文件

#### Scenario: 降级数据源标注

- **WHEN** github-scout通过gh CLI降级获取了数据
- **THEN** 报告的数据源覆盖状态SHALL标注"GitHub: 降级模式（gh CLI），数据可能不完整"

#### Scenario: GitHub数据在报告中体现

- **WHEN** coordinator返回的分类动态列表中包含15条GitHub PR和8条GitHub Issue
- **THEN** 报告的分类动态列表中MUST包含这15条PR和8条Issue

#### Scenario: 数据统计在报告中展示

- **WHEN** coordinator返回的数据统计显示"采集120条 → 融合后95条 → 高价值分析5条"
- **THEN** 报告的数据源覆盖状态部分MUST展示这些统计数字
