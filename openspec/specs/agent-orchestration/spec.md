## ADDED Requirements

### Requirement: Multi-agent拓扑定义

系统SHALL定义以下agent拓扑结构，每个agent以`.opencode/agents/<name>.md`文件形式存在：

- `openinsight-orchestrator`（mode: primary）：主入口agent
- `project-coordinator`（mode: subagent）：项目级协调agent
- `github-scout`（mode: subagent）：GitHub数据采集agent
- `external-source-scout-web`（mode: subagent）：Web数据采集agent
- `external-source-scout-slack`（mode: subagent）：Slack数据采集agent
- `item-analyst`（mode: subagent）：深度分析agent
- `briefing-composer`（mode: subagent）：报告生成agent

#### Scenario: Agent文件结构验证

- **WHEN** 系统部署完成
- **THEN** `.opencode/agents/`目录下存在上述7个agent的markdown定义文件，每个文件包含有效的YAML frontmatter（description, mode, temperature字段）

### Requirement: Intent-Based Agent Description

每个agent的YAML frontmatter中的`description`字段SHALL描述其工作性质（intent），而非绑定具体model。工作性质分类：
- **mechanical-extraction**: 精确的数据采集与工具调用（scouts）
- **deep-reasoning**: 深度分析与推理（item-analyst, project-coordinator）
- **creative-composition**: 内容组织与文字表达（briefing-composer）
- **orchestration**: 流程编排与决策（orchestrator）

`model`字段为可选默认建议，用户可通过环境覆盖。

#### Scenario: Agent description声明intent

- **WHEN** 查看github-scout的frontmatter
- **THEN** description SHALL包含"mechanical-extraction"性质描述（如"Precision data collector for GitHub sources"），而非"Uses claude-sonnet"

### Requirement: Orchestrator编排流程

`openinsight-orchestrator` SHALL按以下顺序编排工作流：
1. 解析用户输入，提取项目名称和时间窗口
2. 读取`projects/<project>.md`加载项目配置
3. 读取用户个性化配置（user-prompt.md）
4. 通过session message模式调用`project-coordinator`，传入项目配置、用户偏好和时间窗口
5. 接收project-coordinator返回的分析结果
6. **生成报告输出路径**：按 `reports/{project}_community_briefing_{YYYY-MM-DD}.html` 格式构造路径，若同名文件已存在则追加序号后缀（`_v2`、`_v3`...）
7. 通过session message模式调用`briefing-composer`，传入分析结果、用户输出偏好和**报告输出路径**
8. 接收并输出最终报告

#### Scenario: 正常编排流程

- **WHEN** 用户在openinsight-orchestrator中输入`@user-prompt.md pytorch 最近7天`
- **THEN** orchestrator依次调用project-coordinator和briefing-composer，最终输出个性化报告到 `reports/pytorch_community_briefing_{当天日期}.html`

#### Scenario: 项目配置不存在

- **WHEN** 用户指定的项目名在`projects/`目录下没有对应配置文件
- **THEN** orchestrator SHALL返回清晰的错误提示，列出可用的项目名称

#### Scenario: 输出路径传递给composer

- **WHEN** orchestrator调用briefing-composer
- **THEN** 调用消息中MUST包含显式的输出文件路径参数，composer根据该路径写入报告

### Requirement: Project-coordinator三阶段调度

`project-coordinator` SHALL执行三阶段调度流程（采集 → 融合验证 → 深度分析）：

**阶段1 — 并行采集**:
1. 根据项目配置中的数据源列表，并行调用对应的scout subagents
2. 收集所有scout的Layer 1+2返回结果

**阶段2 — 融合验证**:
3. 对scout结果执行跨源证据融合（URL-based去重 + 语义关联标记）
4. 对融合后的数据做质量校验（格式完整性、去除明显异常）
5. 输出去重统计和数据源均衡检查结果
6. 结合用户偏好进行价值评估和排序

**阶段3 — 深度分析**:
7. 对排名前N的高价值动态项，为每个创建独立的item-analyst session
8. 每个item-analyst session启动时携带当前wisdom notepad
9. 每个item-analyst返回后，提取wisdom追加到notepad
10. 汇总所有分析结果，**包含完整的分类动态列表和数据统计**，返回给orchestrator

coordinator返回给orchestrator的结果MUST包含以下结构：
```
## 数据统计
- 各scout采集条目数: GitHub: X, Web: Y, Slack: Z
- 融合后总条目数: M
- 高价值分析条目数: N

## 高价值动态深度分析
[按 impact_level 排序的 item-analyst 分析结果列表]

## 分类动态列表
[按 type 分类的所有通过质量校验的动态条目，不仅是高价值项]

## 跨动态洞察（Wisdom Summary）
[从最终 wisdom notepad 提炼的洞察]

## 数据源覆盖状态
[各 scout 的采集状态、降级信息、失败项]
```

#### Scenario: 并行scout调度

- **WHEN** project-coordinator接收到包含GitHub和Web两个数据源的项目配置
- **THEN** coordinator SHALL并行发起github-scout和external-source-scout-web的调用，而非串行等待

#### Scenario: 高价值项筛选含证据融合

- **WHEN** scouts返回共50条动态，其中github-scout和slack-scout各有3条指向同一PR的记录
- **THEN** coordinator SHALL先将这3对记录合并为3条（保留各源互补信息），再对融合后的47条动态进行价值评分

#### Scenario: Wisdom在item-analyst间传递

- **WHEN** 第1个item-analyst分析发现"模块torch.distributed近期有大量重构活动"
- **THEN** 后续 batch 的 item-analyst MAY 收到包含该发现的 wisdom notepad。在 batch 并行模式下，同一 batch 内的 item-analyst 不共享 wisdom（并行取舍），coordinator 在所有 batch 完成后执行跨动态综合补偿。

#### Scenario: 返回结果包含完整分类列表

- **WHEN** scouts共采集80条动态，融合后剩75条通过质量校验，其中5条为高价值项
- **THEN** coordinator返回的分类动态列表MUST包含全部75条，不仅是5条高价值项
