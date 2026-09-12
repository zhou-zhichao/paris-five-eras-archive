# 巴黎与伦敦 — 3D 城市延时动画

[English](README.md) | [简体中文](README.zh-CN.md)

`main` 只维护两个项目：

| 项目 | 保留版本 | 使用说明 |
| --- | --- | --- |
| 巴黎视频复刻版 | `worktree-video-replica` · `88ccaed` | [replica/README.md](replica/README.md) |
| 伦敦 v30 优化版 | `london` · `45e156b` | [london/README.md](london/README.md) |

巴黎沿用 `replica/` 目录，十个地标模型已补齐至 `replica/assets/models/`，不再依赖旧工作目录。伦敦保留最新的沼泽芦苇、Walbrook 河道、码头地形与历史修正。

进入对应目录后，按照项目 README 生成缓存、构建 Blender 场景并渲染。大体积场景、视频、原始 OSM 下载、缓存和安装依赖不进入 Git。巴黎参考视频放在 `reference/PARIS-original-IFhKB5zHWFg.mp4`，仅对照检查需要。操作 Minerva 前需遵守个人 `minerva-slurm` 技能。

巴黎 v50 与另一套参考重建实现已退出主分支文件树；旧预览图和归档清单也已移除。所有分支提交历史通过合并保留，原分支及已有 worktree 保留可追溯，历史大文件仍在原 GitHub Releases。本地已有的忽略文件未删除。

此次整理检查源码语法、数据和模型依赖，没有重新渲染视频。
