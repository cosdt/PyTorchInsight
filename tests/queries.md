# Test Query Set (15 queries)

## Category 1: Time Window Variations

### Q1: Narrow Window (1 day)
```
@user-prompt.md pytorch 最近1天 执行完整工作流生成报告。
```
**Expected**: Fast execution, possibly few or no items. Tests empty/sparse data handling.

### Q2: Standard Window (7 days)
```
@user-prompt.md pytorch 最近7天 执行完整工作流生成报告。
```
**Expected**: Typical run. Baseline for quality and performance comparison.

### Q3: Wide Window (30 days)
```
@user-prompt.md pytorch 最近30天 执行完整工作流生成报告。
```
**Expected**: Large dataset. Tests dynamic N scaling (should select N=5-7), pagination, and effort budget limits.

## Category 2: Different Projects

### Q4: PyTorch project
```
@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。
```
**Expected**: Full data source coverage (GitHub + Discourse + Blog). Multiple scouts active.

### Q5: torch-npu project (downstream)
```
@user-prompt.md torch-npu 最近7天 执行完整工作流生成报告。
```
**Expected**: Cross-project analysis triggered (pytorch as upstream). Downstream Impact section in report.

## Category 3: Edge Cases

### Q6: Empty Data Period
```
@user-prompt.md pytorch 2020-01-01 到 2020-01-02 执行完整工作流生成报告。
```
**Expected**: Dynamic N=0, graceful "no significant activity" message. No crash.

### Q7: Very Recent (today only)
```
@user-prompt.md pytorch 最近0天 执行完整工作流生成报告。
```
**Expected**: Either interpreted as today or error with clear message.

## Category 4: Degradation Scenarios

### Q8: Slack MCP Disabled
```
@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。
```
**Precondition**: Disable Slack MCP in opencode.json (`"enabled": false`).
**Expected**: Scout precheck skips slack-scout. Report marks Slack as failed in data source coverage.

### Q9: MCP Connection Issues
```
@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。
```
**Precondition**: Temporarily misconfigure pytorch-community MCP path.
**Expected**: Scouts degrade to GitHub MCP / gh CLI. Retry-before-degrade behavior. Degradation noted in report.

## Category 5: Role Adaptation

### Q10: Core Developer Role
```
@user-prompt-core-dev.md pytorch 最近7天 执行完整工作流生成报告。
```
**Expected**: Report emphasizes RFC, architecture discussions, foundation activity. Less focus on bug fixes.

### Q11: Default Role (no user-prompt)
```
pytorch 最近7天 执行完整工作流生成报告。
```
**Expected**: Uses default role (general developer). Report balanced across all categories.

## Category 6: Cross-Project Analysis

### Q12: PyTorch with Downstream Impact
```
@user-prompt.md pytorch 最近7天 执行完整工作流生成报告。
```
**Expected**: Item-analyst runs cross-project analysis for downstream repos (Ascend/pytorch). Downstream Impact section appears if impact found.

### Q13: torch-npu Upstream Tracking
```
@user-prompt.md torch-npu 最近7天 执行完整工作流生成报告。
```
**Expected**: Checks pytorch/pytorch as upstream. Version comparison may trigger.

## Category 7: Checkpoint Resume

### Q14: Resume from Partial Run
```
@user-prompt.md pytorch 最近7天 执行完整工作流生成报告。
```
**Precondition**: Run Q2 first, then kill mid-execution. Staging directory has partial data.
**Expected**: Second run detects checkpoint, skips completed phases.

## Category 8: Concurrent Execution

### Q15: Concurrent Runs (via server mode)
```bash
opencode serve --port 4096 &
opencode run --attach http://localhost:4096 --agent openinsight-orchestrator --model alibaba-cn/qwen3.5-plus -- "@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。" &
opencode run --attach http://localhost:4096 --agent openinsight-orchestrator --model alibaba-cn/glm-5 -- "@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。" &
wait
```
**Expected**: Both runs complete without DB lock issues. Staging directories isolated by time_window naming.
