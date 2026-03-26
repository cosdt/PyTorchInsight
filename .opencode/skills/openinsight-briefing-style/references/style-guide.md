# OpenInsight Briefing Style Guide

## 报告格式

报告使用标准 GFM（GitHub Flavored Markdown）语法，确保在 GitHub、编辑器、终端中均可良好渲染。

## 区段结构

使用 `##` 二级标题作为区段分隔，报告包含以下区段：

1. `## Executive Summary`
2. `## 高价值动态详情`
3. `## 跨动态洞察`
4. `## 分类动态列表`
5. `## 数据源覆盖状态`
6. `## 下游影响评估`（条件）
7. `## 报告 Diff`（可选）

## 影响等级视觉标识

| 等级 | 标识 | 用法 |
|------|------|------|
| High | 🔴 | 标题前缀 `### 🔴 [标题](URL)` |
| Medium | 🟡 | 标题前缀 `### 🟡 [标题](URL)` |
| Low | 🟢 | 标题前缀 `### 🟢 [标题](URL)` |

## 高价值动态格式

每条高价值动态使用三级标题 + 元信息列表：

```markdown
### 🔴 [标题](URL)

- **类型**: PR / Issue / Discussion
- **作者**: @author | **日期**: YYYY-MM-DD
- **影响等级**: 🔴 High

分析摘要文本...

- **建议行动**: 关注 / 参与讨论 / 代码审查 / 适配准备
- **信息来源**: PR diff, Discourse discussion
```

## 跨动态洞察格式

使用 Markdown 引用块（`>`）展示洞察：

```markdown
> **模块趋势**: 本周 distributed training 模块有密集重构活动

> **关键人物**: 开发者X在多个模块有活跃贡献
```

## 分类动态列表格式

使用 `<details>` 折叠 + 表格展示：

```markdown
<details open>
<summary>Pull Requests (N)</summary>

| 标记 | 标题 | 日期 | 摘要 |
|------|------|------|------|
| ⭐ | [标题](URL) | YYYY-MM-DD | 一句话摘要 |
| | [标题](URL) | YYYY-MM-DD | 一句话摘要 |

</details>
```

- 第一个分类默认展开（`<details open>`），其余折叠（`<details>`）
- 高价值条目用 ⭐ 标记

## 数据源覆盖状态格式

使用表格展示：

```markdown
| 状态 | 数据源 | 说明 |
|------|--------|------|
| ✅ | GitHub | 正常采集，获取 30 条动态 |
| ⚠️ | GitHub | 降级模式（gh CLI），数据可能不完整 |
| ❌ | Slack | 不可用（MCP 未启用），Slack 讨论数据缺失 |
```

## 降级标注视觉样式

| 状态 | 符号 | 说明 |
|------|------|------|
| 正常 | ✅ | 数据源正常采集 |
| 降级 | ⚠️ | 数据源降级采集，数据可能不完整 |
| 失败 | ❌ | 数据源不可用，相关数据缺失 |

## 高价值标记

在分类动态列表中，被选为高价值的条目用 ⭐ 标记。

## 报告头部

使用一级标题 + 引用块展示元信息：

```markdown
# {{project_name}} 社区动态报告

> 时间窗口：{{time_window}} | 生成日期：{{report_date}}
```

## 报告尾部

使用斜体文本：

```markdown
*由 OpenInsight Multi-Agent System 自动生成 | Powered by OpenCode*
```
