## ADDED Requirements

### Requirement: 版本对比分析

当 PR 的 target branch 不是 main 时，item-analyst SHALL 执行版本对比分析：

1. 确保 PR 所属仓库的 bare clone 可用
2. 创建两个 worktree：main 分支和 target branch
3. 在两个 worktree 中 diff PR 涉及的关键变更文件
4. 推理版本间差异的含义（如：是否已 backport、行为是否一致、签名是否兼容）

#### Scenario: PR target 为 release 分支时触发版本对比

- **WHEN** item-analyst 分析一个 target branch 为 release/2.7 的 PR
- **THEN** item-analyst SHALL 创建 main 和 release/2.7 两个 worktree，diff 关键文件，并在输出中包含 `version_comparison` 字段说明版本差异

#### Scenario: PR target 为 main 时不触发版本对比

- **WHEN** item-analyst 分析一个 target branch 为 main 的 PR
- **THEN** item-analyst SHALL 不执行版本对比分析，`version_comparison` 字段不出现在输出中

#### Scenario: PR target 为 nightly 分支时触发版本对比

- **WHEN** item-analyst 分析一个 target branch 为 nightly 的 PR
- **THEN** item-analyst SHALL 对比 nightly vs main，推理版本间差异含义

### Requirement: 跨项目影响链追踪

当项目配置中存在 `role: downstream` 的仓库时，item-analyst SHALL 对所有 downstream 仓库执行影响链追踪：

1. 从 PR/Issue 提取 changed APIs（函数名、类名、模块路径等）
2. 确保每个 downstream 仓库的 bare clone 可用
3. 在 downstream 仓库中搜索 changed APIs 的使用情况
4. 读取命中文件的上下文代码
5. 推理每处引用的影响程度和风险

搜索策略完全由 agent 自主决定——可以 grep API 名、函数名、模块名，也可以追踪 import 链。

#### Scenario: 上游 API 签名变更影响下游 C++ 调用

- **WHEN** item-analyst 分析 pytorch/pytorch 的一个 PR，该 PR 修改了 `ProcessGroup.allreduce()` 的函数签名，且项目配置中 Ascend/torch-npu 标记为 `role: downstream`
- **THEN** item-analyst SHALL 在 torch-npu 仓库中搜索 `allreduce` 的所有使用位置，识别出 Python 层兼容但 C++ 层会编译失败的风险，并在 `impact_chain` 中记录每处匹配的文件、行号、上下文和风险评估

#### Scenario: 上游变更对下游无影响

- **WHEN** item-analyst 分析 pytorch/pytorch 的一个 PR，该 PR 修改了仅限 CUDA 后端的内部实现，且在 torch-npu 中搜索后无匹配
- **THEN** item-analyst SHALL 在 `impact_chain` 中记录 downstream_repo 的 overall_impact 为 `none`，说明未发现依赖

#### Scenario: 无 downstream repo 配置时不触发

- **WHEN** 项目配置中不存在 `role: downstream` 的仓库
- **THEN** item-analyst SHALL 不执行跨项目影响链追踪

## MODIFIED Requirements

### Requirement: 分析结果结构化输出

item-analyst SHALL 以结构化格式返回分析结果，包含：
- `item_type`: 动态类型（PR/Issue/RFC/Discussion等）
- `item_title`: 原始标题
- `item_url`: 来源链接
- `summary`: 深度分析摘要（200-500字）
- `impact_level`: 影响等级（high/medium/low）
- `impact_areas`: 受影响的模块或领域列表
- `recommended_action`: 建议行动
- `analysis_depth`: 分析深度标记（surface/code-level/cross-project/version-aware，可组合如 cross-project+version-aware）
- `evidence_sources`: 本次分析引用的信息源列表（如"PR diff", "torch-npu source grep", "Discourse discussion"）
- `wisdom_contribution`: 本次分析贡献的可复用发现列表
- `impact_chain`（仅 cross-project 时）: 跨项目影响链详情，包含每个 downstream repo 的匹配列表（file, line, context, risk）和 overall_impact
- `version_comparison`（仅 version-aware 时）: 版本对比结论，包含 base_ref, compare_ref, diff_summary, backport_status

#### Scenario: 输出包含跨项目影响链

- **WHEN** item-analyst 完成跨项目影响链追踪分析
- **THEN** 返回结果 SHALL 包含 `impact_chain` 字段，其中每个 downstream_repo 条目包含 matches 列表和 overall_impact 评级，且 `analysis_depth` 包含 `cross-project`

#### Scenario: 输出包含版本对比结论

- **WHEN** item-analyst 完成版本对比分析
- **THEN** 返回结果 SHALL 包含 `version_comparison` 字段，包含 base_ref、compare_ref、diff_summary 和 backport_status，且 `analysis_depth` 包含 `version-aware`

#### Scenario: 输出结构完整性

- **WHEN** item-analyst 完成对任意动态项的分析
- **THEN** 返回结果 SHALL 包含所有必填字段（item_type, item_title, item_url, summary, impact_level, impact_areas, recommended_action, analysis_depth, evidence_sources, wisdom_contribution），不允许缺失

#### Scenario: 组合分析深度

- **WHEN** item-analyst 同时执行了版本对比和跨项目影响链追踪
- **THEN** `analysis_depth` SHALL 标记为 `cross-project+version-aware`，输出同时包含 `impact_chain` 和 `version_comparison` 字段
