# {{project_name}} 社区动态报告

> 时间窗口：{{time_window}} | 生成日期：{{report_date}}

---

## 概览

{{executive_summary}}

<!--
3-5 句总体摘要。
根据用户角色调整侧重点。
-->

## 重点关注

{{high_value_items}}

<!--
每条高价值动态使用以下结构：

### 🔴 [标题](URL)

- **类型**: PR / Issue / RFC
- **作者**: @author | **日期**: YYYY-MM-DD

分析摘要...

- **建议行动**: 关注 / 跟进 / 适配 / 忽略
- **优先级**: P0 / P1 / P2

> 入选原因: {why_selected}
-->

## 社区动态

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

分类顺序：Pull Requests, Issues, RFC, Discourse 讨论, Blog / 公告, Events
-->

## 关键人物动态

{{key_contributors}}

<!--
社区关键人物的活动摘要。
若无关键人物数据，简要说明并跳过此节内容。
-->

## 附录

{{appendix}}

<!--
数据采集统计和数据源覆盖状态：

| 状态 | 数据源 | 说明 |
|------|--------|------|
| ✅ | GitHub | 正常采集，获取 N 条动态 |
| ⚠️ | Discourse | 降级模式，数据可能不完整 |
| ❌ | Slack | 不可用，Slack 讨论数据缺失 |

数据管道统计：采集 N 条 → 融合后 M 条 → 深度分析 K 条
-->

---

*由 PyTorchInsight Multi-Agent System 自动生成 | Powered by OpenCode*
