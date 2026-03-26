## Context

当前 MCP server 的 Slack token 完全依赖环境变量静态注入。`config.py` 在模块加载时读取 `SLACK_XOXC_TOKEN` / `SLACK_XOXD_TOKEN`，一旦 token 过期，整个 MCP server 进程需要重启并手动更新环境变量。

项目同级目录已有 `slack-token-extractor`（Playwright 版），提供三阶段自动提取：
1. 从 `.slack_tokens.env` 文件加载已保存 token → `auth.test` 验证有效性
2. 从本地 Chrome profile headless 提取（零交互）
3. 交互式浏览器登录 fallback

MCP server 作为 Claude Code 子进程运行，无交互终端，Phase 3 不适用于启动流程。

### 关键约束
- MCP server 通过 stdio 与 Claude Code 通信，启动时不能阻塞太久（Chrome headless ~3-5s）
- `playwright` 是重量级依赖（~150MB Chromium），必须作为可选依赖
- macOS 上 Chrome cookie 使用 Keychain 加密，必须用系统 Chrome（`channel='chrome'`），Playwright bundled Chromium 无法解密
- token 保存文件权限必须 0o600

## Goals / Non-Goals

**Goals:**
- MCP server 启动时自动获取 Slack token，无需用户手动配置环境变量
- token 过期时自动刷新重试，而非直接报错
- Playwright 不可用时优雅降级为环境变量模式
- 将提取逻辑作为项目内部模块，不依赖外部 `slack-token-extractor` 目录

**Non-Goals:**
- 不提供独立的 CLI 命令（如 `setup-slack`）用于交互式登录（后续可选）
- 不支持多 workspace 同时提取
- 不做 token 加密存储（文件权限已足够）
- 不修改 `slack-token-extractor` 上游代码

## Decisions

### D1: 三阶段 token 获取策略

**选择**: env vars → saved file → Chrome auto-extract，三阶段顺序执行

```
SlackConfig.resolve()
    │
    ├─ 1. env vars 已设置? → 直接使用（兼容现有配置）
    │
    ├─ 2. load_tokens_from_file() → validate_tokens()
    │     └─ 有效 → 使用
    │
    ├─ 3. try_extract_from_local_chrome()
    │     └─ 成功 → save_tokens() + 使用
    │
    └─ 4. 全部失败 → slack.available = False，tool 返回配置提示
```

**理由**: env vars 优先保证向后兼容；saved file 是零开销快速路径；Chrome 提取是核心自动化能力。

### D2: token_extractor.py 作为独立内部模块

**选择**: 从 `playwright_extract.py` 提取核心函数到 `src/pytorch_community_mcp/token_extractor.py`

**替代方案**: 直接 import `../slack-token-extractor/playwright_extract.py`

**理由**:
- 外部路径不稳定，部署时可能不存在
- 只需要 5 个核心函数，不需要 CLI 入口和交互式 Phase 3
- 可以统一环境变量命名（`SLACK_MCP_XOXC_TOKEN` → `SLACK_XOXC_TOKEN`）
- 作为内部模块可以更好地做 Playwright 可选依赖检测

### D3: Playwright 作为可选依赖 + 运行时检测

**选择**: `pyproject.toml` 中 `[project.optional-dependencies]` 定义 `slack-auto = ["playwright"]`，运行时 `try: import playwright` 判断是否可用

```python
# token_extractor.py
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
```

**理由**: 不安装 playwright 的用户不受影响，现有功能完全保留。

### D4: SlackConfig 变为可变 + 支持运行时刷新

**选择**: `SlackConfig` 从 `frozen=True` 改为可变 dataclass，新增 `refresh()` 方法

**替代方案**: 保持 frozen，每次刷新创建新 Config 实例

**理由**:
- `SlackClient` 持有 token 引用，需要原地更新
- `SlackClient` 新增 `update_tokens()` 方法，由 `SlackConfig.refresh()` 调用后同步更新
- 刷新逻辑集中在一处，避免散落

### D5: SlackClient 认证失败自动重试

**选择**: `search_messages()` 捕获 `SlackAuthError` 后调用 token 刷新，最多重试一次

```
search_messages()
    │
    ├─ 成功 → 返回结果
    │
    └─ SlackAuthError
         ├─ refresh_callback() 成功 → 重试一次
         └─ refresh_callback() 失败 → 抛出原始异常
```

**替代方案**: 在 tool 层做重试

**理由**: 在 client 层做更内聚，tool 层不需要感知 token 刷新逻辑。通过 callback 解耦 client 和 config。

### D6: Token 文件路径

**选择**: `~/.slack_tokens.env`（与 `slack-token-extractor` 默认路径一致）

**理由**: 如果用户已经用 `slack-token-extractor` CLI 提取过 token，MCP server 可以直接复用，零配置。

## Risks / Trade-offs

**[启动延迟]** → Chrome headless 提取需要 3-5 秒。缓解：Phase 2（saved file）是毫秒级快速路径，只有首次或 token 过期时才走 Phase 3（Chrome 提取）。

**[Chrome 未安装或未登录 Slack]** → Phase 3 失败。缓解：优雅降级为 `slack.available = False`，tool 返回明确提示信息，不影响其他 tool 正常工作。

**[macOS Keychain 权限弹窗]** → 首次用系统 Chrome 读取 cookie 时 macOS 可能弹出 Keychain 授权。缓解：这是一次性操作，且与用户直接运行 `slack-token-extractor` 行为一致。

**[Playwright 版本兼容性]** → Playwright 和系统 Chrome 版本需匹配。缓解：Playwright 的 `channel='chrome'` 使用系统已安装的 Chrome，不依赖 bundled Chromium 版本。

**[SlackConfig 不再 frozen]** → 失去不可变性保证。缓解：仅 `refresh()` 方法修改 token 字段，且在 MCP server 单线程环境下无并发风险。
