## ADDED Requirements

### Requirement: Effort Budget 停止条件

系统 SHALL 对每个 agent 设置 effort budget 停止条件：

| Agent | Budget |
|-------|--------|
| item-analyst | 代码搜索：每个仓库 max 10 次 grep，max 20 次文件读取。跨项目追踪：每个 downstream repo max 5 个文件深入读取。超限返回部分结果并标注 `budget_reached: true` |
| github-scout | max 15 次 tool call |
| web-scout | 每个源 max 5 次 WebFetch 尝试 |
| coordinator | 若 Phase 3 累计超过 10 分钟，跳过剩余 item，汇总已完成的分析 |
| orchestrator | coordinator 超时 15 分钟 → 中止并报告；composer 超时 5 分钟 → 直接输出 coordinator 文本结果 |

#### Scenario: Item-analyst 代码搜索超限

- **WHEN** item-analyst 在单个仓库中已执行 10 次 grep
- **THEN** item-analyst SHALL 停止继续搜索，返回已有结果并标注 `budget_reached: true`

#### Scenario: Coordinator Phase 3 超时

- **WHEN** coordinator 的 Phase 3（深度分析）累计超过 10 分钟
- **THEN** coordinator SHALL 跳过剩余未分析的 item，汇总已完成的分析结果返回

#### Scenario: Orchestrator 超时中止

- **WHEN** coordinator 执行超过 15 分钟
- **THEN** orchestrator SHALL 中止 coordinator 并输出已有的部分结果

### Requirement: Scout 按需裁剪

coordinator SHALL 在 Phase 1 执行 scout 可用性预检：
- 检查 project_config 数据源列表 → 仅调度有配置的 scout
- 检查 Slack MCP 可用性 → 不可用则跳过，节省 subagent 开销
- 记录跳过的 scout 及原因

#### Scenario: Slack 未配置时跳过

- **WHEN** 项目配置中无 Slack 数据源，或 Slack MCP 不可用
- **THEN** coordinator SHALL 跳过 slack-scout 调用，记录"跳过 Slack: 未配置/MCP 不可用"

#### Scenario: 仅 GitHub 数据源

- **WHEN** 项目配置仅包含 GitHub 数据源
- **THEN** coordinator SHALL 仅调用 github-scout，跳过 web-scout 和 slack-scout

### Requirement: Report-Evaluator 集成

orchestrator SHALL 在 composer 完成后调用 report-evaluator 进行质量验证：
- composer → evaluator → pass → 交付
- composer → evaluator → fail → composer 修正（仅 1 次）→ 交付（附注评估结果）

#### Scenario: Evaluator 通过直接交付

- **WHEN** evaluator 对 composer 输出返回 pass
- **THEN** orchestrator SHALL 直接交付报告给用户

#### Scenario: Evaluator 失败触发修正

- **WHEN** evaluator 返回 fail 且指出缺少"跨动态洞察"区段
- **THEN** orchestrator SHALL 将评估反馈传递给 composer 进行修正，修正后交付

### Requirement: Agent 显式任务边界

每个 agent SHALL 遵守 MUST NOT 约束：

| Agent | MUST NOT |
|-------|----------|
| orchestrator | 自行采集数据或执行分析 |
| coordinator | 自行 fetch 数据（通过 scout）；生成最终报告；编造 scout 未返回的数据 |
| scouts | 执行价值判断或分析；summary 超过 50 字 |
| item-analyst | 修改源代码；分析未分配的 item；超出 effort budget 继续搜索 |
| composer | 重新分析 item；裁剪分类动态列表；自造 URL |

#### Scenario: Coordinator 不自行 fetch

- **WHEN** coordinator 需要 GitHub 数据
- **THEN** coordinator MUST 通过 github-scout subagent 获取，不得自行调用 GitHub MCP 工具

#### Scenario: Composer 不裁剪列表

- **WHEN** coordinator 返回 75 条分类动态
- **THEN** composer MUST 在报告中包含全部 75 条，不得自行筛选裁剪

### Requirement: Agent 自验证步骤

以下 agent SHALL 在返回结果前执行自验证：

- **item-analyst**: 检查所有必填 YAML 字段完整；若 `analysis_depth` 含 `cross-project` 则验证 `impact_chain` 存在
- **briefing-composer**: 写入前验证 HTML 5 个区段齐全、URL 来自源数据而非自造
- **coordinator**: 融合后验证去重统计一致性（`before ≥ after`，`merge_count = before - after`）

#### Scenario: Item-analyst 自验证发现缺失字段

- **WHEN** item-analyst 完成分析但 `impact_level` 字段缺失
- **THEN** item-analyst SHALL 在返回前补全该字段，不返回不完整的结果

#### Scenario: Composer 自验证发现 URL 异常

- **WHEN** composer 生成的 HTML 中包含非源数据来源的 URL
- **THEN** composer SHALL 在写入前移除该 URL 或替换为源数据中的正确 URL

## MODIFIED Requirements

### Requirement: Multi-agent拓扑定义

系统SHALL定义以下agent拓扑结构，每个agent以`.opencode/agents/<name>.md`文件形式存在：

- `openinsight-orchestrator`（mode: primary）：主入口agent
- `project-coordinator`（mode: subagent）：项目级协调agent
- `github-scout`（mode: subagent）：GitHub数据采集agent
- `external-source-scout-web`（mode: subagent）：Web数据采集agent
- `external-source-scout-slack`（mode: subagent）：Slack数据采集agent
- `item-analyst`（mode: subagent）：深度分析agent
- `briefing-composer`（mode: subagent）：报告生成agent
- `report-evaluator`（mode: subagent）：报告质量评估agent

#### Scenario: Agent文件结构验证

- **WHEN** 系统部署完成
- **THEN** `.opencode/agents/`目录下存在上述8个agent的markdown定义文件，每个文件包含有效的YAML frontmatter（description, mode, temperature字段）

### Requirement: Project-coordinator三阶段调度

`project-coordinator` SHALL执行三阶段调度流程（采集 → 融合验证 → 深度分析）：

**阶段1 — 并行采集**:
1. 执行 scout 可用性预检，仅调度有配置且可用的 scout
2. 根据项目配置中的数据源列表，并行调用对应的scout subagents
3. Scout 结果写入 staging 目录独立文件（phase1_github.md, phase1_web.md, phase1_slack.md）

**阶段2 — 融合验证**:
4. 读取 staging 目录中的 scout 结果文件
5. 对scout结果执行跨源证据融合（URL-based去重 + 语义关联标记）
6. 对融合后的数据做质量校验（格式完整性、去除明显异常）
7. 输出去重统计和数据源均衡检查结果
8. 结合用户偏好进行价值评估和排序
9. 根据融合结果动态决定高价值项数量 N
10. 融合结果写入 staging/phase2_fusion.md

**阶段3 — 深度分析（batch 并行模式）**:
11. 将高价值项分为 batch（每 batch ≤ 2 个 item）
12. 每个 batch 内的 item-analyst MAY 并行启动（依赖 PoC 验证结果）
13. Item-analyst 结果写入 staging/phase3_item_{n}.md
14. 所有 batch 完成后，执行跨动态综合（coordinator 自身执行），生成 staging/wisdom.md
15. 汇总所有分析结果写入 staging/coordinator_result.md
16. 向 orchestrator 返回 staging 目录路径和摘要统计（≤200 tokens）

coordinator返回给orchestrator的结果MUST仅包含：
- staging 目录路径
- 高价值分析条目数 N
- 融合后总条目数 M
- 各 scout 采集条目数摘要

#### Scenario: 并行scout调度

- **WHEN** project-coordinator接收到包含GitHub和Web两个数据源的项目配置
- **THEN** coordinator SHALL并行发起github-scout和external-source-scout-web的调用，结果分别写入 staging/phase1_github.md 和 staging/phase1_web.md

#### Scenario: Batch 并行 item-analyst

- **WHEN** 融合后有 5 个高价值项需要深度分析
- **THEN** coordinator SHALL 分为 3 个 batch（2+2+1），每 batch 内的 item-analyst MAY 并行执行，batch 间串行

#### Scenario: 动态 N 决策

- **WHEN** 融合后条目数为 25 条
- **THEN** coordinator SHALL 选择 N=3~5（取分数断层以上），而非固定 N=5

#### Scenario: 融合后 0 条

- **WHEN** 融合后有效条目数为 0
- **THEN** coordinator SHALL 设置 N=0，跳过 Phase 3，返回"无显著活动"

#### Scenario: 返回轻量引用而非全量数据

- **WHEN** coordinator 完成所有分析
- **THEN** coordinator 向 orchestrator 返回 ≤200 tokens 的摘要引用，不返回完整分析结果

### Requirement: Orchestrator编排流程

`openinsight-orchestrator` SHALL按以下顺序编排工作流：
1. 解析用户输入，提取项目名称和时间窗口
2. 读取`projects/<project>.md`加载项目配置
3. 读取用户个性化配置（user-prompt.md）
4. **检查 staging 目录**：检查 `reports/.staging/{project}_{date}_{time_window}/` 的 checkpoint 状态
5. 根据 checkpoint 状态决定：跳过 coordinator / 通知 coordinator 部分恢复 / 正常全流程
6. 通过session message模式调用`project-coordinator`，传入项目配置、用户偏好、时间窗口和 staging 目录路径
7. 接收project-coordinator返回的 staging 路径引用
8. **生成报告输出路径**：按 `reports/{project}_community_briefing_{YYYY-MM-DD}.html` 格式构造路径，若同名文件已存在则追加序号后缀
9. 通过session message模式调用`briefing-composer`，传入 staging 目录路径、用户输出偏好和报告输出路径
10. 通过session message模式调用`report-evaluator`，传入报告路径和 staging 目录路径
11. 若 evaluator 返回 fail → 调用 composer 修正（仅 1 次）→ 交付
12. 输出最终报告

#### Scenario: 正常编排流程（含 evaluator）

- **WHEN** 用户在openinsight-orchestrator中输入`@user-prompt.md pytorch 最近7天`
- **THEN** orchestrator依次调用project-coordinator、briefing-composer、report-evaluator，最终输出报告

#### Scenario: Checkpoint 恢复跳过 coordinator

- **WHEN** staging 目录中已存在 coordinator_result.md
- **THEN** orchestrator SHALL 跳过 coordinator 调用，直接调用 composer

#### Scenario: 项目配置不存在

- **WHEN** 用户指定的项目名在`projects/`目录下没有对应配置文件
- **THEN** orchestrator SHALL返回清晰的错误提示，列出可用的项目名称
