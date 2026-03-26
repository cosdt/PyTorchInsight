## ADDED Requirements

### Requirement: 目标导向代码访问策略

item-analyst SHALL 使用目标导向策略访问代码，替代过程规定的 git 命令 runbook：

**目标**: 在指定 git ref 上读取源代码进行静态分析。

**方法**: 使用 `{repo_cache_dir}/{repo_short}.git` bare clone + `git worktree` 检出。

**约束**:
- 首次 clone 使用 `--single-branch` 减少磁盘占用
- 按需 fetch 其他分支
- 分析完成后（无论成功失败）必须清理 worktree
- 永不删除 bare clone 本身

**失败处理**: 任何 git 操作失败 → 记录错误 → 跳过代码级分析 → `analysis_depth: surface`

#### Scenario: 正常代码访问

- **WHEN** item-analyst 需要分析 pytorch/pytorch 某个 PR 的代码
- **THEN** item-analyst SHALL 使用 bare clone + worktree 检出目标分支，完成分析后清理 worktree

#### Scenario: Git 操作失败降级

- **WHEN** worktree 创建失败（如磁盘空间不足）
- **THEN** item-analyst SHALL 记录错误，跳过代码级分析，将 `analysis_depth` 设为 `surface`

### Requirement: 分析结果写入 Staging

item-analyst SHALL 将分析结果写入 staging 目录文件 `staging/phase3_item_{n}.md`，而非通过对话消息返回全量结果。向 coordinator 返回的消息 SHALL 仅包含 item 编号、impact_level 和 wisdom_contribution（≤100 tokens）。

#### Scenario: 结果写入文件

- **WHEN** item-analyst 完成对第 3 个高价值项的分析
- **THEN** item-analyst SHALL 将完整分析结果写入 `staging/phase3_item_3.md`，向 coordinator 返回"item_3: impact=high, wisdom: torch.distributed 模块重构活跃"

## MODIFIED Requirements

### Requirement: Wisdom Notepad消费与贡献

每个item-analyst session SHALL：
1. **消费wisdom**: 在分析开始时，若 coordinator 传入了 wisdom notepad 则读取作为先验知识；在 batch 并行模式下，MAY 不接收 wisdom notepad（打破顺序依赖）
2. **贡献wisdom**: 在分析结束时，在结果中附带`wisdom_contribution`字段，包含本次分析中发现的可复用知识

wisdom_contribution的类型包括：
- `module_insight`: 模块级发现（如"torch.distributed正在大规模重构"）
- `person_pattern`: 人物活动模式（如"@pytorchbot 近期主要在autograd模块活跃"）
- `cross_reference`: 跨动态关联（如"此PR与Issue #12345直接相关"）
- `codebase_pattern`: 代码模式发现（如"该仓库的breaking change通常在utils/目录先出现"）

**Batch 并行模式下的 wisdom 处理**:
- 同一 batch 内的 item-analyst 不互相传递 wisdom
- 所有 batch 完成后，coordinator 读取所有 `phase3_item_*.md` 执行跨动态综合，生成 `staging/wisdom.md`

#### Scenario: Batch 并行模式无 wisdom 输入

- **WHEN** item-analyst 在 batch 并行模式下启动，未收到 wisdom notepad
- **THEN** analyst SHALL 正常执行分析，不依赖先验知识，并在完成后贡献 wisdom_contribution

#### Scenario: 事后跨动态综合

- **WHEN** 所有 item-analyst batch 完成
- **THEN** coordinator SHALL 读取所有 phase3_item_*.md，识别跨 item 的模式（相同作者跨 PR、相同模块密集变更、PR 间引用关系），生成 staging/wisdom.md

#### Scenario: 利用wisdom发现跨item关联

- **WHEN** item-analyst收到wisdom notepad中包含"开发者X正在推进distributed training重构"，且当前分析的PR作者也是开发者X
- **THEN** analyst SHALL在分析中引用此先验知识，将本PR置于更大的重构叙事中评估其影响

#### Scenario: 贡献新wisdom

- **WHEN** item-analyst在分析中发现一个全新的模块依赖关系
- **THEN** analyst SHALL在wisdom_contribution中记录此发现，类型为module_insight

### Requirement: 跨项目影响链追踪

当项目配置中存在 `role: downstream` 的仓库时，item-analyst SHALL 对**每个高价值项**执行影响链追踪，作为核心功能而非条件执行的次要功能：

1. 从 PR/Issue 提取 changed APIs（函数名、类名、模块路径等）
2. 确保每个 downstream 仓库的 bare clone 可用
3. 在 downstream 仓库中搜索 changed APIs 的使用情况
4. 读取命中文件的上下文代码
5. 推理每处引用的影响程度和风险

**核心路径强化**:
- 对每个高价值项，无论其是否直接涉及下游 API，均 SHALL 检查 diff 涉及的文件路径
- 分析深度由 impact 决定，不由类型决定（即使"文档更新"也可能意味着行为变更）
- 每个 downstream repo max 5 个文件深入读取（effort budget）

搜索策略完全由 agent 自主决定。

#### Scenario: 上游 API 签名变更影响下游 C++ 调用

- **WHEN** item-analyst 分析 pytorch/pytorch 的一个 PR，该 PR 修改了 `ProcessGroup.allreduce()` 的函数签名，且项目配置中 Ascend/torch-npu 标记为 `role: downstream`
- **THEN** item-analyst SHALL 在 torch-npu 仓库中搜索 `allreduce` 的所有使用位置，识别风险，并在 `impact_chain` 中记录

#### Scenario: 文档 PR 仍触发跨项目检查

- **WHEN** item-analyst 分析一个标题为"Update torch.distributed docs"的 PR，且项目配置含 downstream repo
- **THEN** item-analyst SHALL 检查该 PR 的 diff 文件路径，若涉及接口模块则在 downstream repo 中搜索相关 API 使用

#### Scenario: 上游变更对下游无影响

- **WHEN** item-analyst 分析 pytorch/pytorch 的一个 PR，该 PR 修改了仅限 CUDA 后端的内部实现，且在 torch-npu 中搜索后无匹配
- **THEN** item-analyst SHALL 在 `impact_chain` 中记录 overall_impact 为 `none`

#### Scenario: 无 downstream repo 配置时不触发

- **WHEN** 项目配置中不存在 `role: downstream` 的仓库
- **THEN** item-analyst SHALL 不执行跨项目影响链追踪
