# LLM-as-Judge Evaluation Framework

## Evaluation Dimensions

### 1. Factual Accuracy (事实准确性)

**Rubric**: Compare report claims against source data in staging directory.

**Prompt**:
```
你是报告质量评估专家。请对比以下报告与源数据，评估事实准确性。

报告文件: {report_path}
源数据目录: {staging_dir}

评估标准:
- 报告中引用的 PR/Issue 编号是否在源数据中存在？
- 报告中描述的变更内容是否与源数据一致？
- 影响等级评估是否合理？

输出:
- accuracy_score: 1-5 (5=完全准确, 1=严重失实)
- inaccuracies: [列出具体不准确项]
```

### 2. Citation Accuracy (引用准确性)

**Rubric**: Verify all URLs and references point to valid sources.

**Prompt**:
```
请验证报告中所有超链接和引用的准确性。

报告文件: {report_path}
coordinator 数据: {staging_dir}/coordinator_result.md

评估标准:
- 所有 URL 是否在 coordinator 数据中存在？（非编造）
- GitHub PR/Issue 链接格式是否正确？
- Evidence sources 引用是否与实际数据源匹配？

输出:
- citation_score: 1-5
- invalid_citations: [列出无效引用]
```

### 3. Completeness (完整性)

**Rubric**: Check all required sections and data items are present.

**Prompt**:
```
请评估报告的内容完整性。

报告文件: {report_path}
coordinator 数据: {staging_dir}/coordinator_result.md

评估标准:
- 是否包含全部 5 个必需区段？
- 分类动态列表是否包含 coordinator 返回的所有条目？
- Executive Summary 是否覆盖了最重要的发现？
- 数据源覆盖状态是否完整？

输出:
- completeness_score: 1-5
- missing_items: [列出缺失项]
```

### 4. Downstream Impact Coverage (下游影响覆盖度)

**Rubric**: Evaluate cross-project analysis quality (if applicable).

**Prompt**:
```
请评估报告的跨项目影响分析质量。

报告文件: {report_path}
item 分析数据: {staging_dir}/phase3_item_*.md

评估标准:
- 是否包含 Downstream Impact 区段（若存在下游仓库配置）？
- 影响项是否按风险等级正确分组？
- 是否提供了具体的文件路径和行号？
- 建议行动是否合理？

输出:
- impact_score: 1-5 (若不适用返回 N/A)
- coverage_gaps: [列出覆盖缺失]
```

## Automated Evaluation Script

```bash
# Run evaluation on a specific report
# Requires: Claude API access or opencode run

REPORT="reports/pytorch_community_briefing_2026-03-23.html"
STAGING="reports/.staging/pytorch_2026-03-23_7d/"

# Evaluate each dimension
for dimension in factual citation completeness impact; do
    opencode run \
        --model alibaba-cn/qwen3.5-plus \
        -- "使用 tests/evaluate.md 中的 ${dimension} 维度评估 ${REPORT}，源数据在 ${STAGING}。输出 JSON 格式的评分结果。" \
        1>"tests/results/eval_${dimension}.json" \
        2>/dev/null
done
```

## Scoring Aggregation

| Dimension | Weight | Pass Threshold |
|-----------|--------|---------------|
| Factual Accuracy | 30% | >= 4 |
| Citation Accuracy | 25% | >= 4 |
| Completeness | 30% | >= 3 |
| Downstream Impact | 15% | >= 3 (or N/A) |

**Overall Pass**: Weighted average >= 3.5 AND no dimension below its threshold.
