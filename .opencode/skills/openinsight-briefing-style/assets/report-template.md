# {{project_name}} 社区动态报告

> 时间窗口：{{time_window}} | 生成日期：{{report_date}}

---

## Executive Summary

{{executive_summary}}

<!--
3-5 个要点，MUST 引用至少一条 GitHub 来源的动态（如有）。
根据用户角色调整侧重点。
-->

## 高价值动态详情

{{high_value_items}}

<!--
每条高价值动态使用以下结构：

### 🔴 [标题](URL)

- **类型**: PR / Issue / Discussion
- **作者**: @author | **日期**: YYYY-MM-DD
- **影响等级**: 🔴 High / 🟡 Medium / 🟢 Low

分析摘要...

- **建议行动**: 关注 / 参与讨论 / 代码审查 / 适配准备
- **信息来源**: PR diff, Discourse discussion
-->

## 跨动态洞察

{{cross_insights}}

<!--
使用引用块展示洞察：

> **模块趋势**: 本周 distributed training 模块有密集重构活动

> **关键人物**: 开发者X在多个模块有活跃贡献
-->

## 分类动态列表

{{categorized_list}}

<!--
每个分类使用 details 折叠：

<details open>
<summary>Pull Requests (N)</summary>

| 标记 | 标题 | 日期 | 摘要 |
|------|------|------|------|
| ⭐ | [标题](URL) | YYYY-MM-DD | 一句话摘要 |
| | [标题](URL) | YYYY-MM-DD | 一句话摘要 |

</details>

<details>
<summary>Issues (N)</summary>

| 标记 | 标题 | 日期 | 摘要 |
|------|------|------|------|
| | [标题](URL) | YYYY-MM-DD | 一句话摘要 |

</details>
-->

## 数据源覆盖状态

{{data_source_status}}

<!--
使用表格展示数据源状态：

| 状态 | 数据源 | 说明 |
|------|--------|------|
| ✅ | GitHub | 正常采集，获取 30 条动态 |
| ⚠️ | GitHub | 降级模式（gh CLI），数据可能不完整 |
| ❌ | Slack | 不可用（MCP 未启用），Slack 讨论数据缺失 |

数据管道统计：采集 N 条 → 融合后 M 条 → 高价值分析 K 条
-->

---

*由 OpenInsight Multi-Agent System 自动生成 | Powered by OpenCode*
