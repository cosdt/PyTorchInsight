## ADDED Requirements

### Requirement: 源权威层级

coordinator SHALL 在价值评估时遵循自然语言源权威优先级：

价值评估时，优先使用一手数据（GitHub PR/Issue/Release、官方 RFC）作为 canonical item。博客文章或 Slack 讨论引用同一 PR 时，PR 为主条目，其余为补充上下文。不得让转述类内容（blog recap、Slack 讨论）在排名中压过其原始源。

#### Scenario: PR 与 Blog recap 引用同一变更

- **WHEN** github-scout 返回 PR#12345，web-scout 返回一篇总结该 PR 的博客文章
- **THEN** coordinator SHALL 将 PR#12345 作为 canonical item 参与价值评估，博客文章作为补充上下文附加在该 item 上

#### Scenario: Slack 讨论引用 RFC

- **WHEN** slack-scout 返回一条讨论某 RFC 的 Slack 线程，web-scout 返回该 RFC 的 Discourse 原文
- **THEN** Discourse RFC 原文 SHALL 作为 canonical item，Slack 讨论作为补充上下文

### Requirement: 动态 N 决策

coordinator SHALL 根据融合结果动态决定高价值项数量 N：
- 融合后 ≤ 10 条: N = min(2, 总数)
- 融合后 11-30 条: N = 3-5（取分数断层以上）
- 融合后 > 30 条: N = 5-7
- 融合后 0 条: N = 0，跳过 Phase 3，返回"无显著活动"

#### Scenario: 少量数据减少分析数

- **WHEN** 融合后仅有 8 条有效动态
- **THEN** coordinator SHALL 设置 N = min(2, 8) = 2，仅对 2 条最高价值项执行深度分析

#### Scenario: 标准数据量

- **WHEN** 融合后有 20 条有效动态，价值评分在第 4 和第 5 名之间存在明显断层
- **THEN** coordinator SHALL 设置 N = 4（取断层以上）

#### Scenario: 零数据

- **WHEN** 融合后有效条目数为 0
- **THEN** coordinator SHALL 设置 N = 0，跳过 Phase 3，直接返回"无显著活动"

### Requirement: 融合结果写入 Staging

coordinator SHALL 将融合后的全量数据写入 `staging/phase2_fusion.md`，包含去重统计、数据源均衡检查结果和排序后的条目列表。

#### Scenario: 融合结果持久化

- **WHEN** coordinator 完成 Phase 2 融合验证
- **THEN** 融合结果 SHALL 写入 `staging/phase2_fusion.md`，包含去重统计和完整条目列表

## MODIFIED Requirements

### Requirement: 多源佐证作为价值信号

在价值评估阶段，`evidence_count > 1`的条目SHALL获得价值加分：
- 一条动态在多个数据源出现，表明其在社区中引起了跨平台关注
- 加分幅度应使原本处于筛选边界的条目更可能被选为高价值项
- 但多源佐证不得使转述类内容（blog recap、Slack 讨论）的排名压过其一手原始源（参见源权威层级要求）

#### Scenario: 多源佐证提升价值排名

- **WHEN** 条目A（evidence_count=3）和条目B（evidence_count=1）的初始价值评分接近
- **THEN** 融合后条目A的最终价值评分SHALL高于条目B，因为多源佐证表明更广泛的社区关注

#### Scenario: 佐证不覆盖源权威

- **WHEN** 一篇博客 recap（evidence_count=3）和其引用的原始 PR（evidence_count=1）
- **THEN** PR 仍然 SHALL 作为 canonical item，博客 recap 的多源佐证不得使其排名超过 PR
