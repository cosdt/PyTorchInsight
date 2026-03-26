## 1. Phase 0: Prompt 精炼（零风险）

- [x] 1.1 为所有 scout agent prompt 添加显式 MCP 工具名映射（get_prs, get_issues, get_rfcs, get_commits 等），包含参数和优先级
- [x] 1.2 为所有 agent prompt 添加 MUST NOT 任务边界约束清单
- [x] 1.3 替换 item-analyst 3.5-3.7 节（~80 行 git 命令 runbook）为目标导向代码访问策略（~20 行）
- [x] 1.4 为 item-analyst、briefing-composer、coordinator 添加自验证步骤
- [x] 1.5 为所有 agent 添加 effort budget 停止条件（item-analyst: 10 grep/20 read, scouts: 15/5 tool calls, coordinator: 10min, orchestrator: 15min/5min）
- [x] 1.6 在 coordinator prompt 中添加源权威层级（自然语言优先级）
- [x] 1.7 在所有 scout prompt 中添加重试优先于降级策略（连续 2 次失败才降级）
- [x] 1.8 验证 opencode.json 默认权限行为，确认 MCP 工具权限后更新配置

## 2. Phase 1: MCP 集成（独立 track，openinsight_mcp 代码库）

- [ ] 2.1 为 `get_prs`/`get_issues`/`get_commits` 添加 `repo` 参数支持多仓库
- [ ] 2.2 修复 `contributors.py` 硬编码的 pytorch/pytorch
- [ ] 2.3 添加 `exclude_bots` 参数（注意 GitHub Search 256 字符限制）
- [ ] 2.4 新增 `get_releases` 工具（releases.py + GitHubClient.get_releases + server.py 注册）
- [ ] 2.5 为 PR/Issue 输出添加 `comments` 计数字段和 `type` 字段
- [ ] 2.6 为 Discourse/Slack/Events 添加分页支持
- [ ] 2.7 修复 Slack client HTTP status 检查（slack.py:73）
- [ ] 2.8 新增 JSON 输出格式选项（formatter.py 添加 format 参数）
- [ ] 2.9 验证 MCP 正常启动（解决 Connection closed 错误）

## 3. Phase 2: 信息流重构 — Staging Artifacts

- [x] 3.1 在 `.gitignore` 中添加 `reports/.staging/` 条目
- [x] 3.2 修改 orchestrator prompt：新增 staging 目录创建和 checkpoint 检查逻辑
- [x] 3.3 修改 coordinator prompt：Phase 1 scout 结果写入 staging 独立文件，Phase 2 融合结果写入 staging/phase2_fusion.md
- [x] 3.4 修改 scout prompt：结果写入 staging 文件，对话消息仅返回 Layer 1 统计摘要
- [x] 3.5 修改 item-analyst prompt：分析结果写入 staging/phase3_item_{n}.md，对话消息仅返回摘要
- [x] 3.6 修改 coordinator prompt：完成后仅返回 staging 路径和摘要统计（≤200 tokens），不返回全量数据
- [x] 3.7 修改 composer prompt：从 staging 目录读取数据文件，而非从 orchestrator 对话消息获取
- [x] 3.8 实现 checkpoint resume：orchestrator 检查 staging 目录状态决定跳过/部分恢复/全流程
- [ ] 3.9 端到端测试：验证 staging 数据流和 checkpoint resume

## 4. Phase 3: 并行化

- [ ] 4.1 PoC 验证：coordinator subagent 能否通过 session() 并行调用 item-analyst subagent
- [x] 4.2 提交 spec change：agent-orchestration spec 中 wisdom notepad 从 SHALL 顺序传递改为 MAY
- [x] 4.3 修改 coordinator prompt：实现 batch 并行 item-analyst（每 batch ≤ 2）
- [x] 4.4 修改 coordinator prompt：新增动态 N 决策逻辑（基于融合后条目数）
- [x] 4.5 修改 coordinator prompt：所有 batch 完成后执行跨动态综合，生成 staging/wisdom.md
- [x] 4.6 修改 coordinator prompt：新增 scout 可用性预检逻辑
- [ ] 4.7 端到端测试：验证并行模式下结果质量和时间改善

## 5. Phase 4: Report-Evaluator

- [x] 5.1 创建 `.opencode/agents/report-evaluator.md` agent 定义文件（mode: subagent, temp: 0.2, evaluation intent）
- [x] 5.2 编写 evaluator prompt：5 项 checklist 评估维度（区段完整性、列表完整性、GitHub 引用、URL 合法性、统计一致性）
- [x] 5.3 修改 orchestrator prompt：composer 完成后调用 evaluator，实现 pass/fail/修正循环（max 1 次）
- [ ] 5.4 端到端测试：验证 evaluator 正常工作（pass 和 fail 场景）

## 6. Phase 5: 跨项目影响增强

- [x] 6.1 修改 item-analyst prompt：跨项目影响分析从条件执行升级为核心路径（对每个高价值项均执行）
- [x] 6.2 修改 item-analyst prompt：分析深度由 impact 决定不由类型决定，文档 PR 也触发跨项目检查
- [x] 6.3 修改 composer prompt：新增第 6 区段 "下游影响评估（Downstream Impact）"，按风险等级分组
- [x] 6.4 修改 composer prompt：新增可选 "报告 Diff" 区段（与前次运行对比）
- [x] 6.5 修改 report-output-contract：HTML 结构支持 7 个区段
- [ ] 6.6 端到端测试：验证 Downstream Impact 区段和报告 Diff 功能

## 7. Phase 6: 评估体系

- [x] 7.1 创建 15 条测试查询集（窄/标准/宽时间窗、不同项目、空数据期、降级、角色适配、跨项目、并发）
- [x] 7.2 编写自动化测试脚本（使用 opencode run 非交互模式）
- [x] 7.3 集成 LLM-as-Judge 评估：事实准确性、引用准确性、完整性、下游影响覆盖度
- [ ] 7.4 运行基准测试并记录结果
