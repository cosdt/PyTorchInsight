# PyTorch Project Config

## Data Sources
- source: https://github.com/pytorch/pytorch
  type: github
  fetcher: github-mcp
  scope: [release, issue, pr, discussion]

- source: https://dev-discuss.pytorch.org/
  type: discourse
  fetcher: webfetch
  scope: [core-discussions, rfc]

- source: https://pytorch.org/blog/
  type: website
  fetcher: webfetch
  scope: [blog, release-highlights]

## Repository Context
- primary_repo: pytorch/pytorch
- related_repos:
  - repo: pytorch/vision
    role: related
  - repo: pytorch/audio
    role: related
  - repo: pytorch/xla
    role: related
  - repo: Ascend/pytorch
    role: downstream
    url: https://gitcode.com/Ascend/pytorch

## Version Mapping
- project_ref: main
  repo_refs:
    - repo: pytorch/pytorch
      ref: main

- project_ref: v2.7.1
  repo_refs:
    - repo: pytorch/pytorch
      ref: v2.7.1

## Local Cache Policy
- local_analysis_enabled: false
- repo_cache_dir: .cache/openinsight/repos
- worktree_dir: .cache/openinsight/worktrees

