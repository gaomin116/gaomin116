---
title: 低配本机 + Cursor 个人知识库方案
tags: cursor, architecture, local-first
---

# 低配本机 + Cursor 个人知识库方案

## 约束

- 只在本机跑数据与索引
- 有 Cursor 订阅（模型与 Agent 编排用云端即可）
- 机器约 8GB 内存 / 256GB 磁盘，避免 Dify / Docker 全家桶
- 尽量把 Cursor 用到边界：Indexing、Rules、本地 MCP

## 架构（三层）

1. **笔记层**：纯 Markdown（本目录）
2. **检索层**：SQLite FTS5 trigram（中英都行，无 embedding）
3. **编排层**：Cursor Agent 通过 MCP 调 `kb_search` / `kb_get`

## 为什么不用向量库

8GB 本机常驻 embedding 模型成本高；FTS5 trigram 对中文短语检索足够，且零依赖。以后语料变大，可再加可选向量通道，不必推翻本结构。

## 日常流程

1. 写笔记到 `kb/`
2. `python3 mcp/kb.py index`（或对话里 `kb_reindex`）
3. 在 Cursor 里用自然语言提问
