## ADDED Requirements

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

### Requirement: 个性化适配

`briefing-composer` SHALL根据用户偏好（来自user-prompt.md）进行个性化适配：
- 根据用户角色调整报告的侧重点（核心开发者侧重社区方向，普通开发者侧重可参与的机会）
- 根据用户关注的模块/领域优先展示相关动态
- 根据用户指定的输出格式生成对应格式

#### Scenario: 核心开发者视角报告

- **WHEN** 用户角色为"核心开发者"，关注社区演进方向
- **THEN** 报告SHALL将RFC、架构讨论、基金会动态等放在显著位置，弱化常规bug fix

#### Scenario: 普通开发者视角报告

- **WHEN** 用户角色为"普通开发者"，关注参与机会
- **THEN** 报告SHALL突出标记good-first-issue、需要review的PR、活跃的Discussion等参与机会

### Requirement: 输出格式支持

系统SHALL通过`openinsight-briefing-style` skill支持以下输出格式：
- **Markdown**: 结构化的 Markdown 文件，使用标准 GFM（GitHub Flavored Markdown）语法，支持标题导航、表格、代码块、`<details>` 折叠
- 后续可扩展Slack通知等格式

#### Scenario: Markdown格式输出

- **WHEN** 用户执行报告生成工作流
- **THEN** briefing-composer SHALL调用openinsight-briefing-style skill生成Markdown文件，文件使用标准GFM语法

#### Scenario: Skill资源引用

- **WHEN** briefing-composer需要生成报告
- **THEN** composer SHALL从`.opencode/skills/openinsight-briefing-style/`中读取Markdown模板和样式指导资源

### Requirement: Briefing Style Skill定义

`openinsight-briefing-style` skill SHALL以标准OpenCode skill格式定义：
- 位于`.opencode/skills/openinsight-briefing-style/SKILL.md`
- frontmatter包含name、description、allowed-tools
- 包含Markdown报告模板（`assets/`目录）
- 包含报告样式指导文档（`references/`目录）

#### Scenario: Skill文件结构

- **WHEN** 系统部署完成
- **THEN** `.opencode/skills/openinsight-briefing-style/`目录SHALL包含SKILL.md及assets、references子目录
