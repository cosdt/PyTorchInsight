## Why

当前报告输出为 HTML 格式，依赖 `openinsight-briefing-style` skill 中的 HTML 模板和 CSS 样式。HTML 格式在实际使用中存在以下问题：
1. **维护成本高**：HTML 模板 + CSS 样式的维护远比 Markdown 复杂，agent prompt 中需嵌入大量 HTML 结构指令
2. **LLM 生成质量不稳定**：LLM 生成 HTML 时容易出现标签不闭合、样式错乱等问题，而 Markdown 语法简单，生成质量更可控
3. **可读性与兼容性**：Markdown 原生可在 GitHub、编辑器、终端中直接阅读，无需浏览器渲染

## What Changes

- **BREAKING**: 报告输出格式从 `.html` 变更为 `.md`（Markdown）
- 移除 `openinsight-briefing-style` skill 的 HTML 模板依赖，改用 Markdown 格式模板
- 更新 `briefing-composer` agent 的输出指令，从生成 HTML 改为生成 Markdown
- 更新 `openinsight-orchestrator` 中的输出路径后缀（`.html` → `.md`）
- 更新 `report-evaluator` 的检查规则，从检查 HTML 区段改为检查 Markdown 区段

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `report-output-contract`: 输出路径格式从 `.html` 改为 `.md`，HTML 区段结构要求改为 Markdown 区段结构
- `report-generation`: 输出格式支持从 HTML 改为 Markdown，Briefing Style Skill 的模板资源从 HTML 改为 Markdown

## Impact

- **Agent 文件**：`briefing-composer.md`、`openinsight-orchestrator.md`、`report-evaluator.md` 需更新输出格式相关指令
- **Skill 资源**：`.opencode/skills/openinsight-briefing-style/` 下的 HTML 模板需替换为 Markdown 模板
- **Spec 文件**：`report-output-contract/spec.md`、`report-generation/spec.md` 需更新格式要求
- **已有报告**：`reports/` 目录下已生成的 `.html` 报告不受影响，但后续新报告将为 `.md` 格式
