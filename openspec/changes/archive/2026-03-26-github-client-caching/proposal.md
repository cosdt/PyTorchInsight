# Proposal: GitHub Client HTTP 持久化缓存

## Why

此 MCP 的核心消费者是 [openinsight](../../../openinsight)。openinsight 的多 agent 架构在单次运行中通过此 MCP 发起大量 GitHub API 调用。list 查询 + detail 查询组合（单次运行 150-200+ HTTP 请求），频繁触发 rate limit（core: 5000/h, search: 30/min），导致请求超时和数据缺失。

关键问题：每次 MCP 进程重启后 in-memory 缓存全部丢失，无法跨 session 复用。而 openinsight 每次运行都会启动新的 MCP 进程，意味着即使两次运行间隔很短、查询相同数据，也会发起完整的 API 调用。

GitHub REST API 原生支持 ETag 条件请求——304 Not Modified 响应不计入 rate limit。利用这一机制可以大幅减少有效 API 配额消耗。

## What Changes

- 添加 **HTTP 级持久化缓存层**（`requests-cache` + SQLite），使 GitHub API 响应能跨 MCP 进程生命周期复用
- 利用 GitHub 的 **ETag/If-None-Match** 条件请求机制，304 响应不消耗 rate limit 配额
- 每个 tool 响应中**附带 API 调用统计**（总请求数、缓存命中数、实际 API 调用数），便于 agent 量化对比此 MCP 与直接使用 GitHub MCP 的请求效率差异
- 现有 tool API 签名完全不变（向后兼容）

## Capabilities

### New Capabilities

- `github-cache`: GitHub API 响应的 HTTP 级持久化缓存机制，支持 ETag 条件请求、per-URL TTL、SQLite 持久化存储、API 调用统计

### Modified Capabilities

- `github-data`: 现有 rate limit handling 间接增强——通过 HTTP 缓存减少实际 API 调用量，降低触发 rate limit 的概率

## Impact

- `src/pytorch_community_mcp/clients/github.py` — 添加缓存安装代码 + API 调用统计 hook
- `src/pytorch_community_mcp/server.py` — 7 个 tool wrapper 添加 stats snapshot/append（tool 实现文件和 formatter.py 无需改动）
- `pyproject.toml` — 添加 `requests-cache >= 1.0` 运行依赖，`responses >= 0.25` 开发依赖
- 新增 SQLite 缓存文件（`~/.cache/pytorch-community-mcp/http_cache.sqlite`）
