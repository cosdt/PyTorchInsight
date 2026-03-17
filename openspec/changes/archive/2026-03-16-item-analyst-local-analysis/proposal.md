## Why

当前 `item-analyst` 的代码分析能力局限于单仓库、单分支的 grep/read 操作（且默认关闭）。面对两个核心场景力不从心：

1. **版本感知分析** — 需要对比 pytorch main 分支与 release/2.7 分支的代码差异，判断某个改动是否已 backport、行为是否一致
2. **跨项目影响链追踪** — 需要发现 pytorch 的某个 API 变更对下游项目（如 torch-npu）的影响，包括 Python 和 C++ 层面的调用关系

## What Changes

- 新增 **bare clone + worktree 管理**基础能力：repo 未 clone 时自动 bare clone，按需创建 worktree 并在分析完成后销毁，session_id 保证并发安全
- 新增 **版本对比分析**：当 PR target branch 不是 main 时，自动创建 main 和 target branch 两个 worktree，diff 关键文件，推理版本间差异含义
- 新增 **跨项目影响链追踪**：当项目配置存在 downstream repo 时，在下游仓库中全量搜索 changed APIs，读取上下文并推理影响程度
- 扩展 `analysis_depth` 枚举：新增 `cross-project`、`version-aware` 及其组合
- 扩展结构化输出：新增 `impact_chain`（跨项目影响详情）和 `version_comparison`（版本对比结论）字段
- 项目配置中新增 `role: downstream` 标记，区分上下游仓库关系

## Capabilities

### New Capabilities

- `repo-management`: Bare clone 生命周期管理、worktree 创建/销毁、并发安全命名、缓存目录策略

### Modified Capabilities

- `item-deep-analysis`: 扩展分析流程（新增 Phase 2 版本对比 + 跨项目影响链追踪 + Phase 3 清理），扩展输出格式（新增 impact_chain、version_comparison 字段、analysis_depth 枚举扩展），新增触发条件逻辑

## Impact

- **Agent 指令文件**: `.opencode/agents/item-analyst.md` 需要增加版本对比和跨项目分析的指令
- **项目配置**: `projects/*.md` 需要支持 `role: downstream` 标记和 worktree 目录配置
- **磁盘 I/O**: bare clone 会占用磁盘空间（pytorch 约 2-3GB），worktree 为轻量级
- **运行时间**: 增加 git clone（首次）和 worktree 创建/diff/搜索的耗时，但 worktree 操作本身很快
- **并发安全**: 多个 item-analyst 实例可同时在同一 bare repo 上创建不同 worktree，git 原生支持此场景
