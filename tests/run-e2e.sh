#!/bin/bash
# OpenInsight Multi-Agent E2E Test Runner
# Usage: ./tests/run-e2e.sh [query_number|all] [model]
# Example: ./tests/run-e2e.sh 2 alibaba-cn/qwen3.5-plus
# Example: ./tests/run-e2e.sh all

set -euo pipefail

MODEL="${2:-alibaba-cn/qwen3.5-plus}"
AGENT="openinsight-orchestrator"
LOG_DIR="tests/results/$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# Test queries (subset - add more as needed)
declare -A QUERIES
QUERIES[1]="@user-prompt.md pytorch 最近1天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。"
QUERIES[2]="@user-prompt.md pytorch 最近7天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。"
QUERIES[3]="@user-prompt.md pytorch 最近30天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。"
QUERIES[4]="@user-prompt.md pytorch 最近3天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。"
QUERIES[5]="@user-prompt.md torch-npu 最近7天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。"

run_query() {
    local qnum="$1"
    local query="${QUERIES[$qnum]}"
    local stdout_log="$LOG_DIR/q${qnum}_stdout.log"
    local stderr_log="$LOG_DIR/q${qnum}_stderr.log"

    echo "=== Running Q${qnum} with model ${MODEL} ==="
    echo "Query: ${query}"
    echo "Logs: ${stdout_log}, ${stderr_log}"

    local start_time=$(date +%s)

    opencode run \
        --agent "$AGENT" \
        --model "$MODEL" \
        --log-level DEBUG \
        -- "$query" \
        1>"$stdout_log" \
        2>"$stderr_log" || true

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo "=== Q${qnum} completed in ${duration}s ==="
    echo "Q${qnum},${MODEL},${duration}s,$(date -Iseconds)" >> "$LOG_DIR/summary.csv"
}

# Parse arguments
QUERY_NUM="${1:-2}"

if [ "$QUERY_NUM" = "all" ]; then
    echo "Running all queries with model: ${MODEL}"
    echo "query,model,duration,timestamp" > "$LOG_DIR/summary.csv"
    for qnum in "${!QUERIES[@]}"; do
        run_query "$qnum"
    done
    echo ""
    echo "=== All queries complete ==="
    echo "Results in: $LOG_DIR"
    cat "$LOG_DIR/summary.csv"
else
    if [ -z "${QUERIES[$QUERY_NUM]+x}" ]; then
        echo "Unknown query number: $QUERY_NUM"
        echo "Available: ${!QUERIES[@]}"
        exit 1
    fi
    echo "query,model,duration,timestamp" > "$LOG_DIR/summary.csv"
    run_query "$QUERY_NUM"
    echo ""
    echo "Results in: $LOG_DIR"
fi
