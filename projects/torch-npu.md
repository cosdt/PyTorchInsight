# torch-npu Project Config

## Data Sources
- source: https://gitcode.com/Ascend/pytorch
  type: gitcode
  fetcher: webfetch


## Repository Context
- primary_repo: Ascend/pytorch
- related_repos:
  - repo: pytorch/pytorch
    role: upstream

## Version Mapping
- project_ref: main
  repo_refs:
    - repo: Ascend/pytorch
      ref: main
    - repo: pytorch/pytorch
      ref: main

- project_ref: v2.7.1
  repo_refs:
    - repo: Ascend/pytorch
      ref: v2.7.1
    - repo: pytorch/pytorch
      ref: v2.7.1

## Local Cache Policy
- local_analysis_enabled: true
- repo_cache_dir: .cache/openinsight/repos
- worktree_dir: .cache/openinsight/worktrees
- default_branch: master

