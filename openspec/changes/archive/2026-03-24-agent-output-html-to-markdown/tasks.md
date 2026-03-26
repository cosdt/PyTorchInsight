## 1. Spec 文件更新

- [x] 1.1 更新 `openspec/specs/report-output-contract/spec.md`：将所有 `.html` 路径引用改为 `.md`，将"HTML 区段结构"改为"Markdown 区段结构"
- [x] 1.2 更新 `openspec/specs/report-generation/spec.md`：将输出格式从 HTML 改为 Markdown，更新 Skill 资源描述

## 2. Agent Prompt 更新

- [x] 2.1 更新 `briefing-composer.md`：将所有 HTML 输出指令改为 Markdown 格式指令，移除 HTML 模板引用，改为 Markdown 模板引用
- [x] 2.2 更新 `openinsight-orchestrator.md`：将输出路径后缀从 `.html` 改为 `.md`
- [x] 2.3 更新 `report-evaluator.md`：将 HTML 区段检查规则改为 Markdown 区段检查规则

## 3. Briefing Style Skill 更新

- [x] 3.1 将 `.opencode/skills/openinsight-briefing-style/assets/` 中的 HTML 模板替换为 Markdown 模板
- [x] 3.2 更新 `.opencode/skills/openinsight-briefing-style/references/style-guide.md` 中的格式说明从 HTML 改为 Markdown
- [x] 3.3 更新 `.opencode/skills/openinsight-briefing-style/SKILL.md` 的描述信息

## 4. 验证

- [x] 4.1 检查所有 agent 文件中不再包含 `.html` 输出路径引用
- [x] 4.2 检查所有 spec 文件中不再包含 HTML 格式要求
