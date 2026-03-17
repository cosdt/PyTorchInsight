## 1. 项目配置扩展

- [x] 1.1 在 `projects/torch-npu.md` 中为 pytorch/pytorch 添加 `role: upstream` 标记，为下游搜索提供配置基础
- [x] 1.2 在 `projects/pytorch.md` 中为 Ascend/pytorch (torch-npu) 添加 `role: downstream` 条目及对应的 repo URL
- [x] 1.3 确认两个项目配置中 `repo_cache_dir` 和 `worktree_dir` 路径统一为 `.cache/openinsight/repos` 和 `.cache/openinsight/worktrees`

## 2. item-analyst 指令增强 — Repo 管理

- [x] 2.1 在 `item-analyst.md` 中新增 bare clone 检查与创建指令：检查 `repo_cache_dir/{repo_short}.git` 是否存在，不存在则 `git clone --bare`
- [x] 2.2 在 `item-analyst.md` 中新增 worktree 创建指令：命名规则 `{repo_short}-{ref_sanitized}-{session_id}`，路径为 `{worktree_dir}/{naming}`
- [x] 2.3 在 `item-analyst.md` 中新增 Phase 3 清理指令：分析完成后 `git worktree remove` 所有本次创建的 worktree

## 3. item-analyst 指令增强 — 版本对比分析

- [x] 3.1 在 `item-analyst.md` 中新增版本对比触发条件判断逻辑：当 PR target branch != main 时触发
- [x] 3.2 新增版本对比执行指令：创建 main 和 target branch 两个 worktree，diff PR 涉及的关键变更文件
- [x] 3.3 新增版本差异推理指令：agent 根据 diff 结果自主推理版本间差异含义（backport 状态、行为一致性、签名兼容性）

## 4. item-analyst 指令增强 — 跨项目影响链追踪

- [x] 4.1 在 `item-analyst.md` 中新增跨项目分析触发条件：检查项目配置中是否存在 `role: downstream` 的仓库
- [x] 4.2 新增下游仓库搜索指令：对每个 downstream repo 确保 bare clone 可用，创建 worktree，全量搜索 changed APIs
- [x] 4.3 新增影响推理指令：读取命中文件上下文，推理每处引用的影响程度和风险等级

## 5. 输出格式扩展

- [x] 5.1 在 `item-analyst.md` 的输出模板中扩展 `analysis_depth` 枚举值：新增 `cross-project`、`version-aware` 及组合形式
- [x] 5.2 新增 `impact_chain` 输出字段定义：包含 downstream_repo、matches（file/line/context/risk）、overall_impact、summary
- [x] 5.3 新增 `version_comparison` 输出字段定义：包含 base_ref、compare_ref、diff_summary、backport_status

## 6. 端到端验证

- [x] 6.1 使用 `opencode run` 对 torch-npu 项目执行端到端测试，验证跨项目影响链追踪功能（选取一个已知影响 torch-npu 的 pytorch PR）
- [x] 6.2 使用 `opencode run` 测试版本对比功能：选取一个 target 为 release 分支的 pytorch PR，验证 version_comparison 输出
- [x] 6.3 验证 `local_analysis_enabled: false` 时行为不变（pytorch 项目配置），确认向后兼容
- [x] 6.4 验证并发安全：同时启动两个 item-analyst 实例分析不同 PR，确认 worktree 路径不冲突
