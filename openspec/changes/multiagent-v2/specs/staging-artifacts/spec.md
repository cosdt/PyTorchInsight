## ADDED Requirements

### Requirement: Staging 目录结构

系统 SHALL 使用 `reports/.staging/{project}_{date}_{time_window}/` 作为 agent 间中间产物存储目录。目录命名规则：
- `{project}`: 项目名称（如 `pytorch`）
- `{date}`: 运行日期（`YYYY-MM-DD`）
- `{time_window}`: 时间窗口（如 `7d`, `1d`, `3d`）

Staging 目录 SHALL 包含以下文件结构：
- `phase1_github.md` — GitHub scout 结果
- `phase1_web.md` — Web scout 结果
- `phase1_slack.md` — Slack scout 结果
- `phase2_fusion.md` — 融合后全量数据
- `phase3_item_{n}.md` — 每个 item-analyst 结果
- `wisdom.md` — 跨动态综合 wisdom notepad
- `coordinator_result.md` — Coordinator 最终输出

每个 scout SHALL 写入独立文件，不得共享同一文件，以消除并行写竞争风险。

#### Scenario: 正常 staging 目录创建

- **WHEN** orchestrator 启动 pytorch 项目最近 7 天的工作流，当前日期为 2026-03-23
- **THEN** 系统 SHALL 创建 `reports/.staging/pytorch_2026-03-23_7d/` 目录

#### Scenario: Scouts 写入独立文件

- **WHEN** github-scout 和 web-scout 并行执行
- **THEN** github-scout 写入 `phase1_github.md`，web-scout 写入 `phase1_web.md`，两者不存在写竞争

### Requirement: 文件引用替代对话中继

Agent 间数据传递 SHALL 使用文件路径引用替代全量对话中继：
- Coordinator 完成后将结果写入 `staging/coordinator_result.md`，仅向 orchestrator 返回路径和摘要统计（≤200 tokens）
- Orchestrator 向 composer 传递 staging 目录路径，composer 自行读取所需文件
- Composer 写入最终报告后，仅向 orchestrator 返回确认和报告路径（≤50 tokens）

#### Scenario: Coordinator 返回轻量引用

- **WHEN** coordinator 完成所有分析
- **THEN** coordinator 向 orchestrator 返回的消息 SHALL 仅包含 staging 目录路径和关键统计（高价值项数、融合后条目数），不包含完整分析结果

#### Scenario: Composer 读取 staging 文件

- **WHEN** orchestrator 调用 composer 时传入 staging 目录路径
- **THEN** composer SHALL 自行读取 `coordinator_result.md` 及其他需要的 staging 文件，不依赖 orchestrator 中继数据

### Requirement: Checkpoint Resume 断点续传

Orchestrator SHALL 在调用 coordinator 前检查 staging 目录状态，支持断点续传：
- 若 `coordinator_result.md` 存在且完整 → 跳过采集和分析阶段，直接调用 composer
- 若 `phase1_*.md` 部分存在 → 通知 coordinator 仅采集缺失的源
- 若 `phase3_item_*.md` 部分存在 → 通知 coordinator 仅分析缺失的 item
- 若无任何 staging 文件 → 正常全流程

用户若需强制重跑，手动删除 staging 目录即可。

#### Scenario: 完整 checkpoint 恢复

- **WHEN** staging 目录中已存在 `coordinator_result.md`
- **THEN** orchestrator SHALL 跳过 coordinator 调用，直接调用 composer，并向用户输出提示说明跳过了采集和分析阶段

#### Scenario: 部分 scout 结果恢复

- **WHEN** staging 目录中存在 `phase1_github.md` 但不存在 `phase1_web.md`
- **THEN** orchestrator SHALL 通知 coordinator 仅需调用 web-scout 和 slack-scout，跳过 github-scout

#### Scenario: 部分 item 分析恢复

- **WHEN** staging 目录中存在 `phase3_item_1.md` 和 `phase3_item_2.md` 但预期有 5 个 item
- **THEN** coordinator SHALL 仅对 item 3/4/5 启动 item-analyst，跳过已完成的 item 1/2

### Requirement: Staging 目录 gitignore

`reports/.staging/` SHALL 被添加到 `.gitignore`，不纳入版本管理。

#### Scenario: gitignore 包含 staging

- **WHEN** 检查 `.gitignore` 文件
- **THEN** `.gitignore` SHALL 包含 `reports/.staging/` 条目
