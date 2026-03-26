## 1. Orchestrator — 报告输出路径硬编码

- [x] 1.1 修改 `openinsight-orchestrator.md`：在"调用 briefing-composer"步骤之前增加"生成报告输出路径"步骤，按 `reports/{project}_community_briefing_{YYYY-MM-DD}.html` 格式构造路径
- [x] 1.2 修改 `openinsight-orchestrator.md`：增加防覆盖逻辑说明——若同名文件已存在，追加 `_v2`/`_v3` 序号后缀
- [x] 1.3 修改 `openinsight-orchestrator.md`：在调用 briefing-composer 的传参列表中增加 `report_output_path` 参数

## 2. Project-Coordinator — 数据传递增强

- [x] 2.1 修改 `project-coordinator.md` 阶段2：在 URL-based 去重中明确"仅完全相同 URL 才合并"，禁止基于标题相似度合并不同 URL 条目
- [x] 2.2 修改 `project-coordinator.md` 阶段2：增加去重统计输出要求（去重前条目数、去重后条目数、合并对数、按数据源分布）
- [x] 2.3 修改 `project-coordinator.md` 阶段2：增加数据源均衡检查——若某数据源条目 fusion 后降幅超 50% 则输出警告
- [x] 2.4 修改 `project-coordinator.md` 汇总返回结构：增加 `## 数据统计` 部分，列出各 scout 采集数、融合后总数、高价值分析数
- [x] 2.5 修改 `project-coordinator.md` 汇总返回结构：明确 `## 分类动态列表` MUST 包含所有通过质量校验的条目，不仅是高价值项

## 3. Briefing-Composer — 数据均衡呈现

- [x] 3.1 修改 `briefing-composer.md` 输入部分：增加 `report_output_path` 参数说明，明确 MUST 使用该路径写入报告
- [x] 3.2 修改 `briefing-composer.md` 分类动态列表部分：增加约束——MUST 包含 coordinator 返回的所有分类条目，不得自行筛选或裁剪
- [x] 3.3 修改 `briefing-composer.md` Executive Summary 部分：增加约束——MUST 引用至少一条 GitHub 来源的动态（如果存在）
- [x] 3.4 修改 `briefing-composer.md` 数据源覆盖状态部分：增加要求展示 coordinator 提供的数据统计信息

## 4. Spec 归档

- [x] 4.1 确认 `openspec/specs/report-output-contract/spec.md` 新 spec 已就绪（由 apply 阶段的 archive 步骤处理）
- [x] 4.2 确认 `evidence-fusion`、`report-generation`、`agent-orchestration` 三个 delta spec 内容与 agent prompt 修改一致
