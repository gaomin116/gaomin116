---
description: 检索并引用 personal-kb 本地 Markdown 知识库
---

# 个人知识库检索（多根、原地索引）

项目文档通常仍在用户自己的目录（如 `D:/项目`），**不要建议复制到 kb/**。

使用 MCP `personal-kb`：

1. `kb_search` — 关键词检索；可用 `root: projects` 限定项目盘
2. `kb_get` — 按逻辑路径读取（优先读原文件）
3. `kb_list` / `kb_stats` / `kb_reindex` — 浏览、诊断、重建索引

回答时附上 `path`（如 `projects/项目A/docs/x.md`）；未命中可提示 `kb_reindex`，而不是搬文件。
