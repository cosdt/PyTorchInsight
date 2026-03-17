本地mermaid渲染最高支持11.12.0版本。

## OpenCode 自动化测试

本项目使用 OpenCode (opencode.ai) 作为 multi-agent 运行时。可通过 `opencode run` 非交互模式自动化测试 agent 工作流，无需手动操作 TUI。

### 命令格式

```bash
opencode run \
  --agent <agent名称> \
  --model <provider/model> \
  --log-level DEBUG \
  -- "<提示词>"
```

### 端到端测试示例

```bash
opencode run \
  --agent openinsight-orchestrator \
  --model alibaba-cn/qwen3.5-plus \
  --log-level DEBUG \
  -- "@user-prompt.md pytorch 最近1天 执行完整工作流生成报告。如果在报告文件目录发现相似报告文件请不要覆盖。" \
  2>/tmp/opencode-test-stderr.log
```

### 可用模型（仅接受以下）

| 模型 | model ID |
|------|----------|
| GLM-5 | `alibaba-cn/glm-5` |
| MiniMax-M2.5 | `alibaba-cn/minimax-m2.5` |
| Kimi K2.5 | `alibaba-cn/kimi-k2.5` |
| Qwen3.5 Plus | `alibaba-cn/qwen3.5-plus` |

### 关键说明

- `--` 分隔符必须放在 flags 和消息之间，否则中文消息可能被误解析为文件路径
- `--file` 用于附加文件，但与中文消息组合时可能有 bug，建议用 `@文件名` 语法直接在消息中引用
- stderr 包含格式化的进度输出（agent 调用链、tool 使用），stdout 包含最终文本结果
- 日志文件位于 `/Users/chu/.local/share/opencode/log/`
- 生成的报告在 `reports/` 目录下
- 典型端到端运行时间：3-8 分钟（取决于模型和数据源数量）
- 可在后台运行并通过 `ps aux | grep opencode` 监控进程状态

### 更多 run 命令 flags

| Flag | 说明 |
|------|------|
| `--continue` | 继续上一个 session |
| `--session <id>` | 继续指定 session |
| `--fork` | fork session 后继续 |
| `--format json` | 输出 JSON 格式事件流 |
| `--file <path>` | 附加文件到消息 |
| `--attach <url>` | 连接到运行中的 `opencode serve` 实例（避免冷启动） |

### 批量测试优化

先启动 headless server 避免每次冷启动：
```bash
opencode serve --port 4096 &
opencode run --attach http://localhost:4096 --agent openinsight-orchestrator --model alibaba-cn/qwen3.5-plus -- "测试消息"
```

## OpenCode 日志分析

日志位于 `/Users/chu/.local/share/opencode/log/`，按启动时间命名（如 `2026-03-16T143237.log`）。**日志文件通常很大（1MB+, 4000+ 行），必须使用 subagent 分析以避免污染主上下文。**

### 日志格式

```
LEVEL  TIMESTAMP +deltaMs service=<service> key=value... event_name
```

### 核心 service 类型及用途

| service | 用途 | 分析价值 |
|---------|------|----------|
| `session` | Session 生命周期（创建、父子关系） | **高** — 重建 agent 调用拓扑 |
| `session.prompt` | 工作流步骤（step=N, loop/exiting/cancel） | **高** — 追踪 agent 执行流程和耗时 |
| `llm` | LLM API 调用（model、agent、mode） | **高** — 统计 API 调用次数和成本 |
| `permission` | 工具调用（read/bash/glob/skill/task） | **中** — 追踪具体操作 |
| `bus` | 事件总线（含 token 流） | **低** — 占 ~70% 行数，纯噪声 |
| `tool.registry` | 工具注册/解析 | **低** — 每步重复，纯噪声 |

### 关键 grep 命令

```bash
LOG="/Users/chu/.local/share/opencode/log/<filename>.log"

# 1. Agent 调用拓扑（session 创建链）
grep 'service=session ' "$LOG" | grep 'created'

# 2. 工作流步骤时间线
grep 'service=session\.prompt' "$LOG" | grep -E '(loop|exiting|cancel)'

# 3. LLM 调用统计
grep 'service=llm' "$LOG"

# 4. 工具使用明细（去掉 ruleset 噪声）
grep 'service=permission' "$LOG" | grep 'evaluated' | grep -v 'ruleset='

# 5. 错误和警告
grep -E '(ERROR|WARN)' "$LOG"

# 6. 噪声分析（各 service 行数分布）
grep -oE 'service=[^ ]+' "$LOG" | sort | uniq -c | sort -rn | head -15

# 7. 总时长（首尾时间戳）
head -1 "$LOG" && tail -1 "$LOG"
```

### Subagent 分析模板

分析日志时，必须启动 subagent 而非在主上下文中直接读取。使用以下 prompt 模板：

```
分析 OpenCode 日志文件 <path>，提取：
1. Session 拓扑（agent 调用链 + parentID）
2. 时间线（各 session 起止时间、各步骤耗时）
3. LLM 调用统计（按 agent 分组计数）
4. 工具使用明细（read/bash/glob/skill/task 各多少次）
5. 错误和警告
6. 工作流质量评估（是否有无效探索、浪费的 LLM 调用、异常重试）
7. 噪声分析（各 service 行数占比）
```

### 已知日志模式

- **bus 噪声**: `message.part.delta`（token 流）占日志 ~60%，分析时应过滤
- **subagent 权限沙箱**: subagent 会被 deny `todowrite`、`todoread`、`task` 权限
- **Session 退出**: 正常退出序列为 `exiting loop` → `cancel` → compaction