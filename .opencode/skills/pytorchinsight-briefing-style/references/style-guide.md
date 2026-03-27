# PyTorchInsight Briefing Style Guide

## 报告格式

报告使用标准 GFM（GitHub Flavored Markdown）语法，确保在 GitHub、编辑器、终端中均可良好渲染。

## 区段结构

使用 `##` 二级标题作为区段分隔，报告包含以下 5 个区段：

1. `## 概览`
2. `## 重点关注`
3. `## 社区动态`
4. `## 关键人物动态`
5. `## 附录`

## 影响等级视觉标识

| 等级 | 标识 | 用法 |
|------|------|------|
| High | 🔴 | 标题前缀 `### 🔴 [标题](URL)` |
| Medium | 🟡 | 标题前缀 `### 🟡 [标题](URL)` |
| Low | 🟢 | 标题前缀 `### 🟢 [标题](URL)` |

## 重点关注 item 格式

每条高价值动态使用三级标题 + 元信息：

```markdown
### 🔴 [标题](URL)

- **类型**: PR / Issue / RFC
- **作者**: @author | **日期**: YYYY-MM-DD

分析摘要文本...

- **建议行动**: 关注 / 跟进 / 适配 / 忽略
- **优先级**: P0 / P1 / P2

> 入选原因: {why_selected}
```

## 可解释性

每条重点关注的 item MUST 包含入选原因说明，使用引用块格式：

```markdown
> 入选原因: 涉及用户关注的 compiler backends 模块，包含 API 变更
```

## 行动建议优先级标识

| 优先级 | 含义 |
|--------|------|
| P0 | 立即行动 |
| P1 | 本周内处理 |
| P2 | 关注即可 |

## 社区动态分类列表格式

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
- 分类顺序：Pull Requests, Issues, RFC, Discourse 讨论, Blog / 公告, Events

## 数据源覆盖状态格式

使用表格展示：

```markdown
| 状态 | 数据源 | 说明 |
|------|--------|------|
| ✅ | GitHub | 正常采集，获取 30 条动态 |
| ⚠️ | Discourse | 降级模式，数据可能不完整 |
| ❌ | Slack | 不可用，Slack 讨论数据缺失 |
```

| 状态 | 符号 | 说明 |
|------|------|------|
| 正常 | ✅ | 数据源正常采集 |
| 降级 | ⚠️ | 数据源降级采集，数据可能不完整 |
| 失败 | ❌ | 数据源不可用，相关数据缺失 |

## 报告头部

```markdown
# {{project_name}} 社区动态报告

> 时间窗口：{{time_window}} | 生成日期：{{report_date}}
```

## 报告尾部

```markdown
*由 PyTorchInsight Multi-Agent System 自动生成 | Powered by OpenCode*
```
