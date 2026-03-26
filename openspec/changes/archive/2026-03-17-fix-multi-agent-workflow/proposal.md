## Why

2026-03-17 端到端测试（pytorch 项目，3 模型并发）暴露了 multi-agent 工作流中的系统性问题：报告输出路径不统一（P0）、GitHub 数据在 coordinator→composer 传递中大量丢失（P0）、采集数据与报告呈现严重不匹配（P1）。这些问题与模型能力无关，属于工作流架构缺陷，直接影响报告的可靠性和实用性。

## What Changes

- **报告输出路径硬编码**：在 orchestrator agent 中明确指定输出路径模板 `reports/{project}_{date}_{model}.html`，消除模型自行决定路径的行为
- **coordinator→composer 数据传递增强**：在 project-coordinator 的返回结构中要求显式包含完整的分类动态列表（含 GitHub PR/Issue 条目），并添加数据传递完整性校验
- **证据融合去重策略优化**：调整 evidence fusion 阶段的去重逻辑，防止将不同 GitHub PR 误判为重复；增加去重前后的条目数统计输出
- **briefing-composer 数据源均衡**：在 composer prompt 中明确要求 GitHub 数据源条目必须在报告中体现，不得因文本丰富度偏好而丢弃
- **数据呈现量下限约束**：当采集条目数远大于报告呈现数时，要求 coordinator/composer 保留更多条目，设置呈现比例下限

## Capabilities

### New Capabilities

- `report-output-contract`: 定义报告输出路径、命名规范和文件管理的标准化约束

### Modified Capabilities

- `evidence-fusion`: 优化去重策略，增加去重前后统计输出，防止过度去重
- `report-generation`: 增加数据源均衡约束和数据呈现量下限要求
- `agent-orchestration`: orchestrator 硬编码输出路径模板并传递给 composer

## Impact

- **Agent prompts**: `openinsight-orchestrator.md`、`project-coordinator.md`、`briefing-composer.md` 均需修改
- **数据流**: coordinator 返回结构增加字段（条目统计、数据完整性标记）
- **向后兼容**: 无 breaking change，现有报告格式不变，仅路径和数据完整性增强
