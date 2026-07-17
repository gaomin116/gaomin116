---
title: personal-kb 项目备忘
tags: projects, personal-kb
---

# personal-kb 项目备忘

目标：在 Cursor 内用本地 MCP 检索个人 Markdown 知识库。

验收：

1. `python3 mcp/kb.py index` 成功
2. `python3 mcp/kb.py search 知识库` 返回笔记
3. Cursor 启用 MCP 后，Agent 能调用 `kb_search`
