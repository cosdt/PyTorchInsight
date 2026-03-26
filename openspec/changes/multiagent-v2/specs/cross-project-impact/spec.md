## ADDED Requirements

### Requirement: Downstream Impact 报告区段

briefing-composer SHALL 在报告中新增第 6 区段 "下游影响评估（Downstream Impact）"，呈现所有具有 cross-project 影响的高价值项：

- 按风险等级分组呈现：
  - 高风险（API 签名变更，编译可能失败）
  - 中风险（行为变更，需验证）
  - 无影响（已检查，未发现下游依赖）
- 每条包含：PR/Issue 编号、变更描述、影响文件路径和行号、建议行动

数据来源为 item-analyst 输出的 `impact_chain` 字段。

#### Scenario: 存在高风险影响项

- **WHEN** item-analyst 分析结果中有 impact_chain 显示 `ProcessGroup.allreduce()` 签名变更影响 torch-npu
- **THEN** 报告 Downstream Impact 区段 SHALL 包含该项，标记为高风险，列出影响的文件路径和行号

#### Scenario: 所有项无下游影响

- **WHEN** 所有高价值项的 impact_chain 均显示 overall_impact 为 none
- **THEN** Downstream Impact 区段 SHALL 显示"已检查 N 个高价值项，未发现下游影响"

#### Scenario: 无 downstream repo 配置

- **WHEN** 项目配置中不存在 downstream 仓库
- **THEN** Downstream Impact 区段 SHALL 不出现在报告中

### Requirement: 跨项目影响作为核心路径

当项目配置存在 `role: downstream` 的仓库时，item-analyst 的跨项目影响分析 SHALL 作为核心功能执行，不再是条件执行的次要功能：

- 对每个高价值项，无论其是否直接涉及下游 API，均 SHALL 检查 diff 涉及的文件路径
- 分析深度由 impact 决定，不由类型决定（即使"文档更新"也可能意味着行为变更）

#### Scenario: 文档 PR 触发跨项目检查

- **WHEN** item-analyst 分析一个标题为"Update torch.distributed docs"的 PR，且项目配置含 downstream repo
- **THEN** item-analyst SHALL 检查该 PR 的 diff 文件路径，若涉及接口文档则在 downstream repo 中搜索相关 API 使用

#### Scenario: 每个高价值项均执行跨项目检查

- **WHEN** coordinator 分配 5 个高价值项给 item-analyst，且项目配置含 downstream repo
- **THEN** 5 个 item-analyst 均 SHALL 执行跨项目影响链追踪，不跳过任何一个

### Requirement: 报告 Diff（与上次报告对比）

当 staging 目录中存在前一次运行的 `coordinator_result.md` 时，briefing-composer MAY 新增 "报告 Diff" 可选区段：
- **新增 item**: 本次出现但上次未出现的条目
- **升级 item**: impact_level 从 low → medium 或 medium → high
- **已解决 item**: 上次出现但本次消失的条目（PR merged / Issue closed）

#### Scenario: 存在前次运行结果

- **WHEN** staging 目录中存在前一次运行的 coordinator_result.md，本次运行发现 3 个新增 PR 和 1 个已 merge 的 PR
- **THEN** 报告 Diff 区段 SHALL 列出 3 个新增 item 和 1 个已解决 item

#### Scenario: 无前次运行结果

- **WHEN** staging 目录中不存在前一次运行的 coordinator_result.md
- **THEN** 报告 Diff 区段 SHALL 不出现在报告中
