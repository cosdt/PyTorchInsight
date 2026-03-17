## Context

OpenInsight 的 `item-analyst` agent 当前通过 grep/read 工具对单仓库进行代码静态分析，受限于：
- 只能访问一个分支（当前 worktree 指向的分支）
- 无法对比 main 与 release 分支间的差异
- 无法追踪上游 API 变更对下游项目的影响

技术栈为 OpenCode (opencode.ai) multi-agent 运行时，agent 指令以 markdown 编写，通过 bash/grep/read 等工具与本地文件系统交互。

项目配置中已预定义了 `local_analysis_enabled`、`repo_cache_dir`、`worktree_dir` 等字段（torch-npu 配置已启用），为本次增强提供了配置基础。

## Goals / Non-Goals

**Goals:**

- item-analyst 能够在 bare clone 上按需创建 worktree，访问任意分支的代码
- 当 PR target branch 不是 main 时，自动对比两个版本的关键文件差异并推理含义
- 当项目配置存在 downstream repo 时，自动在下游仓库中搜索受影响的 API 调用
- 多个 item-analyst 实例可并发运行，worktree 互不冲突
- 分析完成后自动清理 worktree，不留残余

**Non-Goals:**

- 不进行代码编译或运行测试
- 不支持自动提交修复代码或创建 PR
- 不预定义搜索范围或分析深度层级——由 agent 自主决策
- 不管理 bare clone 的自动更新/过期——首次 clone 后由用户手动维护
- 不处理私有仓库的认证问题（假设 agent 运行环境已有访问权限）

## Decisions

### Decision 1: 使用 bare clone + worktree 而非 full clone

**选择**: `git clone --bare` + `git worktree add`

**替代方案**:
- Full clone per branch: 每个分支一份完整 clone。磁盘开销随分支数线性增长，pytorch 单份约 2-3GB
- Sparse checkout: 减少磁盘占用但增加复杂度，且 grep 全量搜索时仍需完整文件树

**理由**: bare clone 只存储 git objects，不检出工作目录，磁盘占用最小。worktree 共享同一份 objects，创建快（秒级）、占用小（仅检出文件）。git 原生支持多个 worktree 并发读取，天然满足并发安全需求。

### Decision 2: worktree 命名使用 session_id 而非随机 ID

**选择**: `{repo_short}-{ref_sanitized}-{session_id}`

**替代方案**:
- UUID: 保证唯一但不可读，难以调试
- 时间戳: 可读但多实例同秒启动时可能冲突

**理由**: OpenCode 的 subagent session ID 天然唯一且可追溯。命名包含 repo 和 ref 信息便于人工排查。即使分析中断残留，也能通过 session_id 关联到具体的运行实例。

### Decision 3: 版本对比仅在 PR target != main 时触发

**选择**: 以 PR 的 target branch 作为触发条件

**替代方案**:
- 始终对比 main vs target: 大量 PR target 就是 main，对比无意义且浪费时间
- 通过配置项手动指定需要对比的分支组合: 增加配置复杂度，且无法预知所有场景

**理由**: target branch 不是 main 的 PR（如 release/2.7, nightly）通常涉及 backport 或版本差异，是版本对比的核心场景。main-to-main 的 PR 不存在版本差异问题。

### Decision 4: 跨项目分析使用 role: downstream 标记而非 related_repos

**选择**: 在项目配置中新增 `role` 字段标记仓库关系方向

**替代方案**:
- 复用现有 `related_repos` 列表: 无法区分上下游方向，不知道该搜索谁
- 在 item-analyst 指令中硬编码仓库列表: 不通用，换项目就失效

**理由**: `role: downstream` 明确表达了依赖方向——当上游 API 变更时，需要在下游仓库中搜索影响。`related_repos` 是对称关系，不携带方向信息。未来可扩展为 `upstream`、`peer` 等角色。

### Decision 5: Agent 自主决定搜索策略，不预定义 impact_surface

**选择**: 不在配置或指令中预定义搜索模式，完全由 agent 根据上下文判断

**替代方案**:
- 预定义 impact_surface 映射表（API → 搜索模式）: 维护成本高，覆盖不全
- 提供搜索模板让 agent 选择: 限制了 agent 的灵活性

**理由**: LLM agent 擅长根据代码变更的语义推断搜索策略。一个函数签名变更可能需要 grep 函数名；一个模块重组可能需要追踪 import 链。预定义模式无法覆盖所有场景，反而会限制 agent 的分析能力。

## Risks / Trade-offs

**[Risk] bare clone 首次下载耗时长** → 仅首次触发，后续复用。pytorch bare clone 约 5-10 分钟（取决于网络）。可考虑在 orchestrator 层面预热，但本期不实现。

**[Risk] 磁盘空间占用** → bare clone（pytorch ~1.5GB）+ worktree（~500MB 每个，用完即删）。对于服务器环境可接受。可通过 `git gc` 定期清理。

**[Risk] worktree 残留（分析中断）** → 残留的 worktree 不影响后续运行（命名唯一）。可在下次运行时检查并清理孤立 worktree，但本期不实现自动清理。

**[Risk] git fetch 未实现自动更新** → bare clone 创建后不会自动 fetch 新 commit。如果分析时 repo 过旧可能遗漏信息。本期依赖用户手动 `git fetch`，后续可增加基于时间的自动 fetch 策略。

**[Trade-off] 搜索完全由 agent 自主决策** → 灵活性高但结果不稳定。同一 PR 不同次分析可能搜索不同关键词得到不同结论。可通过 wisdom notepad 积累搜索经验来缓解。
