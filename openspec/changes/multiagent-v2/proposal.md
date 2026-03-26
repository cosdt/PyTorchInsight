## Why

当前 multi-agent 系统存在 6 个关键差距：MCP 9 工具完全未集成（致命）、对话中继浪费 ~51K tokens（严重）、无断点恢复能力（严重）、item-analyst 串行瓶颈（高）、无停止条件导致无限循环风险（高）、无报告质量评估（高）。同时，系统的核心价值——"告诉我这个上游变更对 torch-npu 意味着什么"——在当前架构中仅是条件执行的次要功能，未被作为核心路径。

## What Changes

- **Phase 0 — Prompt 精炼（零风险）**: 显式工具名映射、MUST NOT 任务边界、目标导向替代过程规定、自验证步骤、effort budget 停止条件、源权威层级、重试优先于降级、opencode.json 权限修复
- **Phase 1 — MCP 集成**: pytorch-community MCP 增强（repo 参数、exclude_bots、get_releases、JSON 输出等）、Scout 降级链重构为 MCP 优先
- **Phase 2 — 信息流重构**: Staging 目录 artifact-based output 替代对话中继、checkpoint resume 断点续传
- **Phase 3 — 并行化**: item-analyst batch 并行（batch≤2）+ 事后跨动态综合、动态 N、Scout 按需裁剪
- **Phase 4 — Report-Evaluator**: 新增质量门禁 agent，checklist 模式评估，最多修正 1 次
- **Phase 5 — 跨项目影响增强**: item-analyst cross-project 分析升级为核心路径、Composer 新增 Downstream Impact 区段、报告 Diff 功能
- **Phase 6 — 评估体系**: 15 条测试查询集、LLM-as-Judge 自动评估

## Capabilities

### New Capabilities
- `staging-artifacts`: Staging 目录文件系统作为 agent 间数据传递机制，替代对话中继，支持 checkpoint resume
- `report-evaluation`: Report-evaluator agent 质量门禁，checklist 评估 + 最多 1 次修正循环
- `cross-project-impact`: 跨项目影响分析作为核心路径，输出 downstream impact 区段和报告 diff

### Modified Capabilities
- `agent-orchestration`: 新增 effort budget 停止条件、Scout 按需裁剪、item-analyst batch 并行模式（wisdom notepad SHALL→MAY）、evaluator 集成
- `data-collection`: Scout 降级链重构为 MCP 优先、显式工具名映射、重试优先于降级策略、MUST NOT 边界
- `evidence-fusion`: 源权威层级（自然语言优先级）、融合后动态 N 决策
- `item-deep-analysis`: 目标导向代码访问策略替代过程规定、自验证步骤、effort budget、cross-project 分析升级为核心功能
- `report-generation`: Composer 新增 Downstream Impact 区段（第 6 区段）、报告 Diff 可选区段、自验证步骤
- `report-output-contract`: 输出格式新增 Downstream Impact 和报告 Diff 区段定义

## Impact

- **Agent prompts**: 所有 6 个 agent prompt 需修改（orchestrator, coordinator, github-scout, web-scout, slack-scout, item-analyst, briefing-composer）+ 新增 report-evaluator
- **MCP 代码库**: `/Users/chu/project/openinsight_mcp` 需增强（独立 track，3-4 天）
- **Spec 文件**: 6 个现有 spec 需 delta 修改 + 3 个新 spec
- **配置**: opencode.json 工具权限、.gitignore 添加 staging 目录
- **运行时行为**: Token 分配从中继转移到评估和新数据（净增约 +5% 单 pass），时间预期从 ~10min 降至 ~5-6min（并行化收益）
