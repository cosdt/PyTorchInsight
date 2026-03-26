## ADDED Requirements

### Requirement: Report-Evaluator Agent 定义

系统 SHALL 新增 `report-evaluator` agent（mode: subagent, temperature: 0.2），作为报告质量门禁。Agent 定义文件位于 `.opencode/agents/report-evaluator.md`，description 标注为 evaluation intent。

#### Scenario: Agent 文件存在

- **WHEN** 系统部署完成
- **THEN** `.opencode/agents/report-evaluator.md` SHALL 存在，frontmatter 包含 description（含 "evaluation" 性质描述）、mode: subagent、temperature: 0.2

### Requirement: Checklist 评估维度

report-evaluator SHALL 使用以下 5 项 checklist 验证报告质量：

1. **区段完整性**: 5 个必需区段（Executive Summary / 高价值详情 / 跨动态洞察 / 分类列表 / 数据源状态）是否齐全
2. **分类列表完整性**: 分类动态列表条目数 ≥ coordinator 返回的 fusion 后条目数
3. **GitHub 引用存在性**: Executive Summary 引用了 GitHub 源（若 coordinator 数据含 GitHub 条目）
4. **URL 格式合法性**: 所有 URL 格式合法，不含 hallucinated URL
5. **数据统计一致性**: 报告中数据统计与 coordinator 数据一致

评估模式为 checklist 验证，不执行深度 LLM 推理。

#### Scenario: 报告通过所有检查

- **WHEN** report-evaluator 对生成的报告执行 5 项 checklist 验证，全部通过
- **THEN** evaluator SHALL 返回 pass 结果

#### Scenario: 报告缺少区段

- **WHEN** 生成的报告缺少"跨动态洞察"区段
- **THEN** evaluator SHALL 返回 fail 结果，指明缺失的区段名称

#### Scenario: URL 格式异常

- **WHEN** 报告中包含格式不合法的 URL（如 `github.com/org/repo/pull/undefined`）
- **THEN** evaluator SHALL 返回 fail 结果，列出异常 URL

### Requirement: 修正循环限制

Orchestrator 的 evaluator 集成 SHALL 限制修正循环最多 1 次：
- Evaluator 返回 pass → 直接交付报告
- Evaluator 返回 fail → composer 修正（仅 1 次机会）→ 交付（附注评估结果）
- 第 2 次评估仍 fail → 交付当前版本 + 附注问题列表

#### Scenario: 首次评估通过

- **WHEN** evaluator 对 composer 首次输出返回 pass
- **THEN** orchestrator SHALL 直接交付报告，不触发修正

#### Scenario: 首次评估失败后修正成功

- **WHEN** evaluator 首次返回 fail，composer 修正后再次评估返回 pass
- **THEN** orchestrator SHALL 交付修正后的报告

#### Scenario: 两次评估均失败

- **WHEN** evaluator 首次返回 fail，composer 修正后再次评估仍返回 fail
- **THEN** orchestrator SHALL 交付当前版本报告，并在输出中附注评估发现的问题列表

### Requirement: Evaluator Budget

report-evaluator 每次评估 SHALL 在 30 秒内完成。

#### Scenario: 评估超时

- **WHEN** evaluator 执行超过 30 秒
- **THEN** 视为 pass，不阻塞报告交付
