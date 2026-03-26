## Context

OpenInsight 是基于 OpenCode multi-agent runtime 的社区动态监控系统，当前架构使用 7 个 agent（orchestrator → coordinator → 3 scouts + item-analyst + composer）通过对话消息中继数据。系统存在 6 个关键差距：MCP 未集成、对话中继浪费 ~51K tokens、无断点恢复、串行瓶颈、无停止条件、无质量评估。核心价值主张——"上游变更对 torch-npu 意味着什么"——在当前架构中仅是次要功能。

**约束**:
- OpenCode subagent 对 `task` 权限默认 deny，并行化需验证 `session()` 机制
- pytorch-community MCP 是独立代码库（`/Users/chu/project/openinsight_mcp`），修改周期独立
- CLAUDE.md 建议并发 ≤ 2
- 用户选择质量优先，接受 evaluator 的 token 代价

## Goals / Non-Goals

**Goals:**
- 将 pytorch-community MCP 9 个工具集成为 scout 首选数据源
- 用 staging 文件系统替代对话中继，消除 orchestrator ~51K token 压力
- item-analyst 从串行改为 batch 并行（batch≤2），预期 -40~50% 时间
- 新增 report-evaluator 质量门禁，checklist 模式，最多 1 次修正
- 跨项目影响分析升级为核心路径，报告新增 Downstream Impact 区段
- 所有 agent 添加 effort budget 停止条件，消除无限循环风险

**Non-Goals:**
- 动态路由（UX 审查确认用户从不发快速查询，routing 解决不存在的问题）
- GitHub Discussions GraphQL 集成（需新 client，推迟到后续迭代）
- Events 数据源（UX 审查建议推迟）
- MiniMax-M2.5 模型支持（当前不可用）
- Token 总量节省（v2 是 token 重分配方案，不是节省方案）

## Decisions

### D1: 分阶段交付，Phase 0 零风险先行

**选择**: 6 个 Phase 按依赖关系排列，Phase 0（prompt 精炼）零风险立即执行，Phase 1（MCP）独立 track。

**理由**: 对抗性审查指出 plan 引用 "simplicity first" 却一次性引入 10+ 新机制。先做零风险 prompt 改进验证方向，再投入架构变更。Phase 0 不改运行时、不改数据流，纯 prompt 修改。

**替代方案**: 一次性全面重构 → 风险过高，回滚困难。

### D2: Staging 目录作为 artifact-based output

**选择**: `reports/.staging/{project}_{date}_{time_window}/` 存储中间产物，agent 间传递文件路径引用而非全量数据。

**理由**: Anthropic 推荐 "subagents store work in external systems, pass lightweight references back"。Scouts 写独立文件（`phase1_github.md`, `phase1_web.md`, `phase1_slack.md`）消除并行写竞争。命名使用 `{project}_{date}_{time_window}` 使相同查询的 resume 自动生效。

**替代方案**:
- 继续对话中继 → orchestrator ~51K token 压力不变
- 数据库/KV store → 过度工程，OpenCode runtime 无原生支持

### D3: Batch 并行（batch≤2）而非全并行

**选择**: item-analyst 分 batch 执行，每 batch ≤ 2 个并行，batch 间串行。

**理由**: CLAUDE.md 建议并发 ≤ 2（实测 3 路并发慢模型性能退化 +26-36%）。N=5 全并行超限。Wisdom notepad 打破顺序依赖，改为事后综合。

**替代方案**:
- 保持串行 → 时间不变，~10 分钟瓶颈
- 全并行 N=5 → 超并发限制，性能退化
- Spec change 前置：wisdom notepad SHALL → MAY（`agent-orchestration` spec 需修改）

### D4: Checklist 评估而非深度推理

**选择**: report-evaluator 使用 5 项 checklist 快速验证，temperature=0.2，≤30 秒 budget。

**理由**: Token 审查指出 evaluator 成本 pass=~38K / 1-fail=~111K。Checklist 模式（结构验证、条目计数、URL 格式）减少 LLM 推理开销。最多修正 1 次消除无限循环风险。

**替代方案**: 深度推理评估 → token 成本过高，收益不成比例。

### D5: MCP 优先降级链

**选择**: Scout 降级链重构为 pytorch-community MCP → GitHub MCP → gh CLI → WebFetch。

**理由**: pytorch-community MCP 提供 9 个工具（get_prs, get_issues, get_rfcs, get_commits 等），返回结构化数据。当前完全未使用。重试优先于降级（连续 2 次失败才降级）。

**替代方案**: 保持当前降级链 → 丢失 MCP 结构化数据优势。

### D6: 自然语言源权威层级

**选择**: 用自然语言引导（"优先使用一手数据作为 canonical item"）替代数值系数（1.0/0.8/0.6）。

**理由**: 对抗审查指出数值系数是 premature abstraction，LLM 无法精确执行权重计算。自然语言更符合 LLM prompt 工作方式。

**替代方案**: 数值权重系统 → LLM 执行不精确，调优困难。

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| coordinator 无法并行调用 item-analyst（subagent 权限） | Phase 3 前置 PoC 验证；若失败保持串行或将调用上移到 orchestrator |
| MCP 增强延期（独立代码库） | Phase 0 不依赖 MCP；工具映射先指向 MCP，降级到 GitHub MCP/gh CLI |
| 并行 wisdom 质量下降（丧失顺序累积） | 事后综合补偿；spec change 保留 MAY use sequential 选项 |
| Report-evaluator fail 场景 token 成本 +111K | 最多修正 1 次上限；checklist 模式减少推理开销 |
| Staging 文件与并发运行冲突 | 命名含 time_window，不同查询自然隔离 |

## Migration Plan

1. **Phase 0**（Day 1-2）: 纯 prompt 修改，git commit 即可回滚
2. **Phase 1**（Day 1-5, 独立 track）: MCP 代码库独立修改，参数有默认值向后兼容
3. **Phase 2**（Day 3-5）: Staging 目录引入，.gitignore 添加 `reports/.staging/`
4. **Phase 3**（Day 3-5）: 需先通过 PoC + spec change；若 PoC 失败保持串行
5. **Phase 4**（Day 5-6）: 新增 agent，不影响现有流程；evaluator 可通过 orchestrator prompt 开关
6. **Phase 5**（Day 3-6）: 增强现有 item-analyst，向后兼容
7. **Phase 6**（Day 7+）: 测试和评估，不改变生产行为

**回滚**: 所有 agent 变更在 git 中，`git revert` 即可。MCP 变更向后兼容（参数有默认值）。

## Open Questions

1. **PoC 结果待验证**: coordinator subagent 能否通过 `session()` 并行调用 item-analyst subagent？OpenCode `task` 权限对 subagent 是 deny 的
2. **opencode.json 默认权限**: 当前系统正常运行，MCP 权限可能是 permissive-by-default，修改前需验证避免破坏
3. **MCP Connection closed 错误**: 实施审查发现 pytorch-community MCP 启动时有连接错误，需在 Phase 1 前解决
