## Context

2026-03-17 端到端测试中，3 个模型（Qwen3.5 Plus、GLM-5、Kimi K2.5）对 pytorch 项目运行完整工作流，暴露了以下系统性问题：

1. **报告输出路径不统一**（P0）：3 个模型分别将报告写入不同目录和命名格式，自动化流程无法可靠定位
2. **GitHub 数据丢失**（P0）：scout 采集了大量 GitHub PR/Issue，但最终报告中 GitHub 数据严重缺失（Qwen: 0 条，Kimi: 5 条，GLM-5: 16 条）
3. **采集量与呈现量严重不匹配**（P1）：Kimi 采集 220 PR + 38 Issue 但仅呈现 8 条，信息损失率 >95%

当前架构：orchestrator → project-coordinator（scouts → fusion → analysis）→ briefing-composer。问题分布在 orchestrator（路径）、coordinator（fusion + 数据传递）、composer（数据均衡呈现）三层。

## Goals / Non-Goals

**Goals:**
- 报告输出路径 100% 可预测，自动化流程可靠定位
- GitHub 数据源条目在最终报告中有明确体现（不为 0）
- 采集数据到报告呈现的信息损失率从 >95% 降至合理范围
- 所有修改通过 agent prompt 层面完成，无需代码变更

**Non-Goals:**
- 不解决并发执行稳定性问题（P1，属于 opencode 运行时层面，需 server 模式）
- 不解决 Kimi K2.5 日期占位符问题（P1，属于模型行为，需模型层面调优）
- 不解决并发日志隔离问题（P2，属于 opencode 基础设施）
- 不重构 agent 拓扑或数据流架构

## Decisions

### D1: 输出路径由 orchestrator 硬编码并传递给 composer

**选择**: orchestrator 在调用 briefing-composer 时，显式指定输出文件路径 `reports/{project}_community_briefing_{date}.html`，composer MUST 使用该路径写入报告。

**替代方案**: 在 composer prompt 中单独硬编码路径模板 → 被否决，因为 orchestrator 拥有项目名称和日期的完整上下文，由其统一决定路径更可靠。

**替代方案**: 在 opencode 配置层面约束输出目录 → 被否决，opencode 无此功能。

**理由**: 路径命名中不包含 model ID，因为 orchestrator 不感知具体模型；日期使用 YYYY-MM-DD 格式确保排序友好。

### D2: coordinator 返回结构增加完整分类动态列表和统计数据

**选择**: 在 coordinator 的返回结构中增加：
1. 显式的 `## 数据统计` 部分，列出各 scout 的采集条目数、fusion 后条目数、最终呈现条目数
2. `## 分类动态列表` 中 MUST 包含所有通过质量校验的条目（不仅是高价值项）

**理由**: 当前 coordinator 返回结构已包含"分类动态列表"，但测试表明模型在实际执行时大量裁剪。增加统计数据可让 orchestrator/composer 感知数据损失，增加显式指令可约束模型不随意裁剪。

### D3: evidence fusion 增加去重保护和统计输出

**选择**:
1. URL-based 去重仅合并**完全相同 URL** 的条目，不对 URL 相似但不同的条目执行合并
2. 去重后 MUST 输出统计：`去重前 N 条 → 去重后 M 条（合并 K 对）`
3. 新增**数据源均衡检查**：如果某数据源的条目在 fusion 后数量下降超过 50%，MUST 发出警告

**理由**: 测试中观察到不同 GitHub PR 被误合并（可能是标题相似但 URL 不同），增加严格 URL 匹配和统计输出可追踪去重行为。

### D4: composer 增加数据源均衡约束和呈现量下限

**选择**:
1. composer 在生成"分类动态列表"时，MUST 包含 coordinator 返回的**所有**分类条目，不得自行筛选或裁剪
2. 对于 GitHub 来源的条目，MUST 在报告中以 PR/Issue 类别明确呈现，不得因文本丰富度偏好将其降级
3. Executive Summary 中 MUST 引用至少一条 GitHub 来源的动态（如果存在）

**替代方案**: 设置固定的呈现条目数下限（如 ≥20 条）→ 被否决，因为不同时间窗口采集量差异大，固定下限不灵活。

**理由**: 测试表明 composer 在生成时偏好 Blog/Discourse 来源（因为文本更丰富、更适合叙事），导致 GitHub 条目被隐性过滤。显式约束可纠正此偏好。

## Risks / Trade-offs

**[报告变长]** 要求 composer 呈现所有分类条目会增加报告长度 → 使用折叠 UI（已有支持）缓解，分类列表部分默认折叠

**[prompt 膨胀]** 增加更多约束指令会增大 agent prompt token 消耗 → 新增指令控制在 200 tokens 以内，影响可忽略

**[模型遵从度]** prompt 层面的约束依赖模型遵从能力，弱模型可能仍然不遵守 → 通过统计数据输出提供事后审计能力，便于发现和定位问题
