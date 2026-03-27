# PyTorchInsight

自动采集 PyTorch 社区动态，生成**个性化情报简报**——让你每天花 5 分钟就能掌握社区里与你相关的高价值信号。

## 它能给你什么？

PyTorchInsight 自动从 GitHub、Discourse 论坛、PyTorch 官网等数据源采集社区活动，经过 AI 多轮筛选和分析后，生成一份**针对你的角色和关注领域定制的 Markdown 报告**。


## 快速开始

### 前置条件

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/)
- [OpenCode](https://opencode.ai)
- GitHub Personal Access Token（[获取方式](https://github.com/settings/tokens)，至少需要 repo 读取权限）

### 1. 安装依赖

```bash
git clone https://github.com/cosdt/PyTorchInsight.git
cd PyTorchInsight
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的凭据：

| 变量 | 描述 | 必需 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub PAT | 否 |
| `DISCOURSE_API_KEY` | Discourse API KEY | 否 |
| `DISCOURSE_API_USERNAME` | Discourse 用户名（与 API Key 配对） | 否 |

### 3. 配置 OpenCode

```bash
cp opencode.json.example opencode.json
```

编辑 `opencode.json`，将 `<path-to-pytorchinsight>` 替换为本项目的绝对路径，将 `<your-github-pat>` 替换为你的 GitHub Token。

### 4. 创建你的用户画像

```bash
cp user-prompt.example.md user-prompt.md
```

编辑 `user-prompt.md`，描述你的角色和关注领域。这决定了报告为你突出哪些内容、过滤哪些噪声。

### 5. 生成报告

```bash
opencode run \
  --agent pytorchinsight-orchestrator \
  --model alibaba-cn/qwen3.5-plus \
  -- "@user-prompt.md pytorch 最近1天 执行完整工作流生成报告。"
```

报告输出到 `reports/` 目录。

## GitHub Actions 自动化部署

项目支持通过 GitHub Actions 自动定时生成周报（每周一 UTC 02:00），也可手动触发。

### 配置 Secrets

在仓库 **Settings → Secrets and variables → Actions → New repository secret** 中添加以下两个 secret：

| Secret | 描述 | 获取方式 |
|--------|------|----------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key | [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) → API-KEY 管理 |
| `GH_PAT` | GitHub Personal Access Token | [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) → Generate new token，勾选 `repo` 权限 |

> **注意**：`GH_PAT` 用于 MCP Server 调用 GitHub API 获取社区数据。workflow 推送报告使用的是 GitHub Actions 默认的 `GITHUB_TOKEN`，无需额外配置。

### 手动触发

1. 进入仓库的 Actions 页面
2. 选择 **Weekly Community Report** workflow
3. 点击 **Run workflow**
4. 可选填写 `project`（默认 pytorch）和 `time_window`（默认 最近7天）

### 失败通知

建议在仓库 Settings → Notifications 中开启 workflow failure 邮件通知，以便及时发现流水线异常。

## 独立使用 MCP Server

PyTorchInsight 的 MCP Server 可以脱离多 Agent 工作流，单独配合 Claude Code 等 MCP 客户端使用，按需查询 PyTorch 社区数据。

提供 10 个工具：

| 工具 | 数据源 | 说明 |
|------|--------|------|
| `get_prs` | GitHub | 按时间范围和模块获取 PR |
| `get_issues` | GitHub | 按时间范围、模块和状态获取 Issue |
| `get_commits` | GitHub | 按时间范围和作者获取 Commit |
| `get_rfcs` | GitHub | 获取 pytorch/pytorch 和 pytorch/rfcs 的 RFC |
| `get_pr_detail` | GitHub | 获取单个 PR 详情（文件变更、Review） |
| `get_issue_detail` | GitHub | 获取单个 Issue 详情（评论、关联 PR） |
| `get_discussions` | Discourse | 搜索论坛话题 |
| `get_events` | pytorch.org | 获取社区活动 |
| `get_blog_news` | pytorch.org | 获取博客和公告 |
| `get_key_contributors_activity` | GitHub + Discourse | 关键贡献者跨平台活动 |

### 在 Claude Code 中使用

参考 `.mcp.json.example`，将 MCP 配置添加到你的 Claude Code 中：

```bash
cp .mcp.json.example .mcp.json
```

编辑 `.mcp.json`，将 `<path-to-pytorchinsight>` 替换为本项目的绝对路径。确保已完成[环境变量配置](#2-配置环境变量)，然后就可以在 Claude Code 中直接查询 PyTorch 社区数据了。

### 直接启动 MCP Server

```bash
uv run pytorch-community-mcp
```

## 架构概览

PyTorchInsight 由两层组成：

```
┌─────────────────────────────────────────────────┐
│  Multi-Agent 工作流（分析层）                      │
│                                                 │
│  Orchestrator (编排)                             │
│    ├── GitHub Collector      (并行采集)           │
│    ├── Community Collector   (并行采集)           │
│    ├── Analyst × 3           (并行深度分析)        │
│    └── Composer              (个性化报告)         │
│                                                 │
├─────────────────────────────────────────────────┤
│  MCP Server（数据层）                              │
│                                                 │
│  pytorch-community-mcp                          │
│  10 个 PyTorch 社区数据工具                        │
│  数据源：GitHub API / Discourse / pytorch.org     │
└─────────────────────────────────────────────────┘
```

- **MCP Server**：领域专用的 [MCP](https://modelcontextprotocol.io/) server，将 PyTorch 社区多个数据源封装为 10 个语义化工具。详见 [MCP Server 文档](docs/mcp.md)。
- **Multi-Agent 工作流**：运行在 [OpenCode](https://opencode.ai) 上的 5 个 Agent 协作系统，负责采集编排、数据融合、深度分析和报告生成。详见 [Multi-Agent 工作流文档](docs/multiagent.md)。

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 启动 MCP Server（开发模式）
uv run pytorch-community-mcp
```

## 文档

| 文档 | 说明 |
|------|------|
| [MCP Server 详细文档](docs/mcp.md) | MCP Server 的设计思路、API 说明 |
| [Multi-Agent 工作流](docs/multiagent.md) | Agent 拓扑、工作流阶段、通信协议 |
| [环境搭建指南](docs/setup.md) | 详细的安装配置步骤 |
| [需求规格](docs/requirement.md) | 产品需求、用户画像、数据源定义 |

## License

Apache-2.0
