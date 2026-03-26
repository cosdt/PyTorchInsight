## ADDED Requirements

### Requirement: Bare Clone 生命周期管理

item-analyst SHALL 在需要访问本地仓库代码时，确保目标仓库的 bare clone 可用。

- 检查 `repo_cache_dir` 下是否存在对应仓库的 bare clone
- 若不存在，执行 `git clone --bare --single-branch --branch <default_branch> <repo_url> <repo_cache_dir>/<repo_short>.git`
- `<default_branch>` 取自项目配置中的 `default_branch` 字段；若未指定，通过 `git ls-remote --symref <repo_url> HEAD` 查询
- MUST 使用 `--single-branch` 仅克隆默认分支，避免拉取上游全部分支（大型仓库可能有数千个分支，如 pytorch 有 5961 个）
- bare clone 创建后可跨 session 复用，不随单次分析结束而删除

#### Scenario: 首次访问未缓存的仓库

- **WHEN** item-analyst 需要分析 pytorch/pytorch 的代码，且 `repo_cache_dir/pytorch.git` 不存在
- **THEN** item-analyst SHALL 执行 `git clone --bare --single-branch --branch <default_branch>` 将仓库克隆到 `repo_cache_dir/pytorch.git`，然后继续后续分析流程

#### Scenario: 访问已缓存的仓库

- **WHEN** item-analyst 需要分析 pytorch/pytorch 的代码，且 `repo_cache_dir/pytorch.git` 已存在
- **THEN** item-analyst SHALL 直接使用已有的 bare clone，不重复克隆

### Requirement: 按需 Fetch 非主分支

由于 bare clone 仅包含 main 分支，当版本对比分析需要访问其他分支（如 `release/2.7`）时，item-analyst SHALL 先按需 fetch 该分支：
```bash
git -C <repo_cache_dir>/<repo_short>.git fetch origin <ref>:<ref>
```

- fetch 成功后方可创建该分支的 worktree
- 若 fetch 失败（分支不存在），SHALL 记录警告并跳过该分支的相关分析

#### Scenario: 版本对比需要非主分支

- **WHEN** item-analyst 需要对比 main 和 release/2.7，但 bare clone 仅包含 main
- **THEN** item-analyst SHALL 先执行 `git fetch origin release/2.7:release/2.7`，再创建 release/2.7 的 worktree

#### Scenario: 非主分支不存在

- **WHEN** item-analyst 尝试 fetch 一个不存在的分支名
- **THEN** item-analyst SHALL 记录警告，跳过版本对比分析，将 analysis_depth 回退为 `code-level`

### Requirement: Worktree 创建与命名

item-analyst SHALL 通过 `git worktree add` 在 bare clone 上创建临时工作目录，用于检出特定分支的代码。

worktree 命名规则 SHALL 为：`{repo_short}-{ref_sanitized}-{session_id}`
- `repo_short`: 仓库名称（如 pytorch, torch-npu）
- `ref_sanitized`: 分支/tag 名称，`/` 替换为 `_`（如 release_2.7）
- `session_id`: 当前 OpenCode subagent session ID

worktree 路径 SHALL 为：`{worktree_dir}/{naming}`

#### Scenario: 创建 main 分支的 worktree

- **WHEN** item-analyst 需要检出 pytorch 的 main 分支代码，当前 session_id 为 sess_a1b2c3
- **THEN** item-analyst SHALL 创建 worktree 于 `{worktree_dir}/pytorch-main-sess_a1b2c3/`

#### Scenario: 创建含斜杠的分支名的 worktree

- **WHEN** item-analyst 需要检出 pytorch 的 release/2.7 分支
- **THEN** item-analyst SHALL 将分支名中的 `/` 替换为 `_`，创建 worktree 于 `{worktree_dir}/pytorch-release_2.7-{session_id}/`

### Requirement: Worktree 清理

item-analyst SHALL 在分析完成后（无论成功或失败）清理本次 session 创建的所有 worktree。

- 使用 `git worktree remove` 删除每个本次创建的 worktree
- 即使部分 worktree 清理失败，SHALL 继续清理其余 worktree 并输出分析结果

#### Scenario: 正常分析完成后清理

- **WHEN** item-analyst 完成版本对比分析，创建了 pytorch-main 和 pytorch-release_2.7 两个 worktree
- **THEN** item-analyst SHALL 在输出分析结果前，依次执行 `git worktree remove` 删除这两个 worktree

#### Scenario: 残留 worktree 不影响后续运行

- **WHEN** 上一次 item-analyst 因异常中断未清理 worktree，新的 item-analyst 实例启动
- **THEN** 新实例 SHALL 使用自己的 session_id 创建新 worktree，与残留 worktree 路径不冲突

### Requirement: 并发安全

多个 item-analyst 实例 SHALL 能够同时在同一个 bare clone 上创建不同的 worktree，互不干扰。

- 每个实例的 worktree 路径因 session_id 不同而唯一
- 不使用文件锁或其他显式同步机制，依赖 git 原生的并发支持

#### Scenario: 两个 item-analyst 同时分析同一仓库的不同 PR

- **WHEN** item-analyst A (session sess_aaa) 和 item-analyst B (session sess_bbb) 同时需要访问 pytorch 的 main 分支
- **THEN** A 创建 `pytorch-main-sess_aaa/`，B 创建 `pytorch-main-sess_bbb/`，两者独立运行互不阻塞
