---
name: pytorchinsight-briefing-style
description: "Generates well-structured Markdown community briefing reports with executive summaries, deep analysis details, cross-item insights, and data source coverage status."
allowed-tools:
  - Read
  - Write
  - Glob
---

# PyTorchInsight Briefing Style

你是报告样式生成技能，负责将结构化的社区动态分析结果组织为结构清晰的 Markdown 报告。

## 使用方式

composer agent 在生成报告时调用此 skill。

## 资源文件

- `assets/report-template.md`: Markdown 报告模板，包含 5 章节结构和占位符
- `references/style-guide.md`: 报告样式指导文档，定义区段格式、标识符号、折叠规范

## 报告生成指令

### 1. 读取模板

从 `assets/report-template.md` 读取 Markdown 模板结构。

### 2. 填充内容

将分析结果填充到模板对应区域：
- `{{executive_summary}}` → 概览内容
- `{{high_value_items}}` → 重点关注内容（含入选原因）
- `{{categorized_list}}` → 社区动态分类列表
- `{{key_contributors}}` → 关键人物动态
- `{{appendix}}` → 附录（数据采集统计和数据源覆盖状态）
- `{{report_date}}` → 报告生成日期
- `{{time_window}}` → 时间窗口描述
- `{{project_name}}` → 项目名称

### 3. 样式应用

参照 `references/style-guide.md` 中的规范：
- 使用影响等级 emoji 标识（🔴🟡🟢）
- 使用 `<details>` 折叠分类列表
- 使用引用块展示入选原因
- 降级数据源使用 ⚠️/❌ 标识

### 4. 输出

生成标准 GFM Markdown 文件，无外部依赖。文件保存到 orchestrator 指定的路径。
