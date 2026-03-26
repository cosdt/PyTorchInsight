## Context

当前 OpenInsight 的报告输出链路：
1. `openinsight-orchestrator` 生成 `.html` 输出路径 → 传递给 `briefing-composer`
2. `briefing-composer` 调用 `openinsight-briefing-style` skill 获取 HTML 模板和样式 → 生成 HTML 报告
3. `report-evaluator` 检查 HTML 报告是否包含 5 个必需区段

涉及的文件：
- `.opencode/agents/briefing-composer.md` — 核心输出 agent
- `.opencode/agents/openinsight-orchestrator.md` — 路径生成
- `.opencode/agents/report-evaluator.md` — 质量检查
- `.opencode/skills/openinsight-briefing-style/` — 模板和样式资源
- `openspec/specs/report-output-contract/spec.md` — 输出路径 spec
- `openspec/specs/report-generation/spec.md` — 报告生成 spec

## Goals / Non-Goals

**Goals:**
- 将报告输出格式从 HTML 替换为 Markdown
- 更新所有相关 agent prompt 中的格式指令
- 更新 spec 文件中的格式要求
- 更新或替换 briefing-style skill 中的模板资源

**Non-Goals:**
- 不改变报告的内容结构（5 个必需区段 + 2 个条件区段保持不变）
- 不改变 agent 间的调用流程和协作模式
- 不迁移已生成的 `.html` 历史报告
- 不引入新的渲染工具或格式化依赖

## Decisions

### Decision 1: 直接替换，不做格式共存

**选择**：一次性将 HTML 格式替换为 Markdown，不保留 HTML 输出能力。

**理由**：
- 维护两套模板增加复杂度，且当前无同时需要两种格式的场景
- agent prompt 中同时描述两种格式会增加 token 消耗和生成歧义

**替代方案**：保留 HTML 作为可选格式 → 放弃，因维护成本高且无实际需求。

### Decision 2: Markdown 报告保留相同的区段结构

**选择**：5 个必需区段 + 2 个条件区段的结构在 Markdown 中用 `##` 标题表示，功能等价。

**理由**：报告的信息架构不变，仅表达格式从 HTML 标签变为 Markdown 语法。

### Decision 3: Briefing Style Skill 模板更新

**选择**：将 skill 中的 HTML 模板替换为 Markdown 模板，style-guide 相应更新。

**理由**：skill 是 composer 的格式参考来源，必须同步更新。

## Risks / Trade-offs

- **[视觉表达能力下降]** → Markdown 不支持折叠、锚点导航等 HTML 特性。Mitigation: 使用 Markdown 的 `<details>` 标签（GitHub Flavored Markdown 支持）保留折叠能力；锚点由 `##` 标题自动生成。
- **[已有报告格式不一致]** → 历史 `.html` 报告与新 `.md` 报告共存。Mitigation: 不影响功能，`reports/` 目录可同时包含两种格式。
- **[Evaluator 规则更新遗漏]** → report-evaluator 仍按 HTML 规则检查 Markdown 报告。Mitigation: 本次变更同步更新 evaluator 的检查规则。
