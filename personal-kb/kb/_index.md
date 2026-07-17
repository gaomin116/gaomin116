---
title: 个人知识库使用说明
tags: meta, getting-started
---

# 个人知识库使用说明

这是 `personal-kb` 的示例笔记。把 Markdown 放进本目录树即可被索引。

## 目录

| 目录 | 用途 |
|------|------|
| `inbox/` | 快速捕获，稍后整理 |
| `topics/` | 按主题沉淀的长期笔记 |
| `projects/` | 与具体项目相关的备忘 |
| `refs/` | 摘录、书摘、链接摘要 |

## 在 Cursor 里怎么问

1. 打开本仓库（或把 `personal-kb` 加进 multi-root workspace）
2. 确认 MCP `personal-kb` 已启用（Customize → Tools & MCP）
3. 对话里直接问：「知识库里关于 XXX 的笔记有哪些？」

Agent 应调用 `kb_search` / `kb_get`，并引用路径回答。
