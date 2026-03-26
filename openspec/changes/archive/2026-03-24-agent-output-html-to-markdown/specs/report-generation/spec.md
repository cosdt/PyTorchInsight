## MODIFIED Requirements

### Requirement: 输出格式支持

系统SHALL通过`openinsight-briefing-style` skill支持以下输出格式：
- **Markdown**: 结构化的 Markdown 文件，使用标准 GFM（GitHub Flavored Markdown）语法，支持标题导航、表格、代码块、`<details>` 折叠
- 后续可扩展 Slack 通知等格式

#### Scenario: Markdown 格式输出

- **WHEN** 用户执行报告生成工作流
- **THEN** briefing-composer SHALL 调用 openinsight-briefing-style skill 生成 Markdown 文件，文件使用标准 GFM 语法

#### Scenario: Skill 资源引用

- **WHEN** briefing-composer 需要生成报告
- **THEN** composer SHALL 从 `.opencode/skills/openinsight-briefing-style/` 中读取 Markdown 模板和样式指导资源

### Requirement: Briefing Style Skill定义

`openinsight-briefing-style` skill SHALL以标准OpenCode skill格式定义：
- 位于`.opencode/skills/openinsight-briefing-style/SKILL.md`
- frontmatter包含name、description、allowed-tools
- 包含 Markdown 报告模板（`assets/` 目录）
- 包含报告样式指导文档（`references/` 目录）

#### Scenario: Skill文件结构

- **WHEN** 系统部署完成
- **THEN** `.opencode/skills/openinsight-briefing-style/` 目录SHALL包含 SKILL.md 及 assets、references 子目录，assets 中包含 Markdown 模板文件
