## MODIFIED Requirements

### Requirement: URL-Based跨源去重

project-coordinator SHALL在收到所有scout结果后，对动态条目执行URL-based去重：
- 提取每条动态的`url`字段
- **仅完全相同URL**的条目合并为一条，保留各源的互补信息（如GitHub提供PR diff摘要，Slack提供开发者讨论观点）
- URL相似但不完全相同的条目（如同一PR的不同URL形式）不得自动合并，MUST保持为独立条目
- 合并后条目的`evidence_count`字段记录原始出现次数，作为重要性信号

去重完成后，coordinator MUST输出统计信息：
```
## 去重统计
- 去重前条目数: N
- 去重后条目数: M
- 合并对数: K
- 按数据源分布: GitHub: X, Discourse: Y, Blog: Z, Slack: W
```

#### Scenario: 同一PR出现在GitHub和Slack

- **WHEN** github-scout返回PR#12345的条目（URL: github.com/org/repo/pull/12345），slack-scout也返回包含相同URL的讨论
- **THEN** coordinator SHALL将两条合并为一条，`evidence_count=2`，摘要整合GitHub的技术变更描述和Slack的开发者讨论要点

#### Scenario: 无重复时正常通过

- **WHEN** 三个scout返回的所有条目URL均不重复
- **THEN** 所有条目SHALL直接进入价值评估阶段，`evidence_count=1`

#### Scenario: URL相似但不同的条目不合并

- **WHEN** github-scout返回 PR#100（URL: github.com/org/repo/pull/100）和 PR#101（URL: github.com/org/repo/pull/101），两者标题相似
- **THEN** coordinator SHALL NOT将两条合并，两条MUST作为独立条目参与价值评估

#### Scenario: 去重统计输出

- **WHEN** scouts共返回50条动态，其中3对URL完全相同被合并
- **THEN** coordinator MUST输出统计：去重前50条 → 去重后47条（合并3对），并附按数据源的分布数据

## ADDED Requirements

### Requirement: 数据源均衡检查

evidence fusion完成后，coordinator SHALL执行数据源均衡检查：
- 统计每个数据源在fusion前后的条目数
- 如果任一数据源的条目在fusion后数量下降超过50%，MUST在输出中发出警告
- 警告格式：`⚠️ 数据源均衡警告: {source}的条目从{N}条降至{M}条（降幅{P}%），请检查去重逻辑`

#### Scenario: GitHub条目大量减少触发警告

- **WHEN** github-scout返回30条PR/Issue，fusion后仅剩12条GitHub来源条目
- **THEN** coordinator MUST输出警告：`⚠️ 数据源均衡警告: GitHub的条目从30条降至12条（降幅60%），请检查去重逻辑`

#### Scenario: 正常去重无警告

- **WHEN** 各数据源条目在fusion后数量下降均未超过50%
- **THEN** coordinator SHALL NOT输出均衡警告
