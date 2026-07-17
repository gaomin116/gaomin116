# personal-kb — 本机个人知识库（Cursor + MCP）

面向：**Cursor 会员、8GB 低配本机、不想装 Dify** 的本地 Markdown 知识库检索。

## 设计要点

| 层 | 选型 | 原因 |
|----|------|------|
| 笔记 | Markdown + 可选 YAML front matter | 零锁死、Git 友好 |
| 检索 | SQLite FTS5 `tokenize='trigram'` | 中英可用、无 embedding、stdlib |
| 编排 | Cursor Agent + 本地 stdio MCP | 发挥会员能力，本机只跑轻进程 |
| 依赖 | **仅 Python 3 标准库** | 8+256 友好，无需 pip/Docker |

```text
你（自然语言）
    ↓
Cursor Agent（订阅模型）
    ↓ MCP tools
personal-kb server（本机，常驻内存极小）
    ↓
SQLite FTS5 ←── mcp/kb.py index ←── kb/**/*.md
```

## 快速开始

```bash
cd personal-kb
python3 mcp/kb.py index
python3 mcp/kb.py search 知识库
python3 mcp/kb.py get topics/cursor-kb.md
python3 mcp/kb.py stats
```

### 接入 Cursor

1. 用 Cursor 打开**本仓库根目录**，或单独打开 `personal-kb/`
2. 已提供配置：
   - 仓库根：`.cursor/mcp.json`
   - 子项目：`personal-kb/.cursor/mcp.json`
3. 打开 **Customize → Tools & MCP**，启用 `personal-kb`
4. 新开 Agent 对话，试问：`知识库里关于 Cursor 的笔记有哪些？`

规则已写在 `personal-kb/.cursor/rules/kb.mdc`（若打开的是仓库根，可把该规则复制到根 `.cursor/rules/`，或把 `personal-kb` 加为 multi-root）。

## MCP 工具

| 工具 | 作用 |
|------|------|
| `kb_search` | 全文检索，返回 path / title / snippet |
| `kb_get` | 按相对路径读全文 |
| `kb_list` | 按前缀列出笔记 |
| `kb_stats` | 索引统计 |
| `kb_reindex` | 从磁盘重建索引 |

## 目录约定

```text
personal-kb/
  kb/
    inbox/      # 速记
    topics/     # 主题
    projects/   # 项目
    refs/       # 摘录 / 术语
  mcp/
    indexer.py  # 建索引
    server.py   # MCP stdio
    kb.py       # CLI
    run_server.sh
  data/         # kb.sqlite（gitignored）
  .cursor/      # mcp / rules / skills
```

笔记可用 front matter：

```markdown
---
title: 标题
tags: a, b
---

# 标题
正文…
```

## 低配建议

- 不要在本机跑大 embedding / 本地 LLM；检索用 FTS，推理用 Cursor
- 语料很大时用 `.cursorignore` 排除无关目录，并定期 `kb.py index`
- 磁盘紧：`data/kb.sqlite` 通常远小于原文；笔记可放移动硬盘，设环境变量：

```bash
export PERSONAL_KB_ROOT=/path/to/your/notes
export PERSONAL_KB_DB=/path/to/kb.sqlite
```

## 演进路线（可选，非必须）

1. **现在**：FTS5 + MCP（本仓库）
2. **以后**：给 `kb_search` 加标签过滤 / 时间过滤
3. **再以后**：可选 sqlite-vec 向量通道（仍可不装 Dify）

## 验收清单

- [x] 无第三方 Python 依赖即可 index / search
- [x] 示例笔记可被中文查询命中
- [x] MCP 配置与 Rules / Skill 模板齐备
