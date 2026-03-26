## ADDED Requirements

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

### Requirement: 语义关联标记

对于URL不同但可能相关的动态（如Discourse RFC和对应的GitHub Issue），coordinator SHALL进行语义关联标记：
- 基于标题关键词相似度识别潜在关联
- 关联条目标记为`related_items`列表，而非强制合并
- 关联关系在报告中展示，帮助用户看到事件的完整图景

#### Scenario: RFC与对应Issue关联

- **WHEN** web-scout返回一条标题为"RFC: New Tensor Subclass API"的Discourse帖子，github-scout返回一条标题为"[RFC] Implement Tensor Subclass API"的Issue
- **THEN** coordinator SHALL将两条标记为related_items，但保持为独立条目，各自参与价值评估

#### Scenario: 无明显关联

- **WHEN** 动态条目的标题之间无关键词重叠
- **THEN** 不进行关联标记，条目保持独立

### Requirement: 数据质量校验

coordinator SHALL在融合后对数据执行质量校验：
- **格式完整性**: 每条动态的6个必填字段均存在且非空
- **时间窗口校验**: 动态日期在请求的时间窗口内
- **异常检测**: 标记明显异常的条目（如summary为空或过短、URL格式无效）
- 校验失败的条目标记为`quality_flag: warning`，不直接丢弃，由coordinator在价值评估时降权

#### Scenario: 缺失字段的条目

- **WHEN** 某条动态缺少`author`字段
- **THEN** coordinator SHALL标记`quality_flag: warning`并在价值评估时对该条目降权，而非丢弃

#### Scenario: 超出时间窗口的条目

- **WHEN** 请求的时间窗口为最近7天，但某条动态的date为30天前
- **THEN** coordinator SHALL将该条目标记为`quality_flag: out_of_range`并从价值评估中排除

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

### Requirement: 多源佐证作为价值信号

在价值评估阶段，`evidence_count > 1`的条目SHALL获得价值加分：
- 一条动态在多个数据源出现，表明其在社区中引起了跨平台关注
- 加分幅度应使原本处于筛选边界的条目更可能被选为高价值项

#### Scenario: 多源佐证提升价值排名

- **WHEN** 条目A（evidence_count=3）和条目B（evidence_count=1）的初始价值评分接近
- **THEN** 融合后条目A的最终价值评分SHALL高于条目B，因为多源佐证表明更广泛的社区关注
