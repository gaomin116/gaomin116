# personal-kb — 本机个人知识库（Cursor + MCP）

面向：**Cursor 会员、8GB 低配本机、不想装 Dify**；文档可继续放在 **D 盘项目目录**，**不必复制**到知识库文件夹。

## 你的顾虑：必须把文档挪出来吗？

**不必。** 正确做法是「原地索引」：

| 做法 | 是否推荐 | 原因 |
|------|----------|------|
| 复制到 `kb/` 再检索 | 不推荐 | 双份维护，增删改要做两遍，无法坚持 |
| 剪切/搬迁到知识库 | 不推荐 | 破坏现有「按项目分文件夹」的管理习惯 |
| **配置多根目录，直接扫描 `D:/项目`** | **推荐** | 目录结构不变；索引只存检索副本；原文仍是唯一真相 |
| 符号链接/目录联接 | 可选 | Windows 可用 junction，但多根配置更直观 |

数据流：

```text
D:/项目/项目A/docs/*.md   ──┐
D:/项目/项目B/*.md        ──┼──► 扫描（不复制）──► SQLite FTS 索引
personal-kb/kb/*.md       ──┘         │
                                      ▼
                              Cursor Agent（MCP: kb_search / kb_get）
                                      │
                              kb_get 优先「现场读原文件」
```

- **增删改**：只在项目文件夹操作一次  
- **检索侧**：定期 `python3 mcp/kb.py index`（或对话里 `kb_reindex`）同步索引  
- **读全文**：`kb_get` 优先读磁盘原文件，改完立刻能读到最新内容（不必为了「读」而先复制）

## 设计要点

| 层 | 选型 | 原因 |
|----|------|------|
| 原文 | 仍在各项目目录 | 保持你的项目管理方式 |
| 检索 | SQLite FTS5 `trigram` | 中英可用、无 embedding、stdlib |
| 编排 | Cursor Agent + 本地 MCP | 发挥会员能力；本机只跑轻进程 |
| 依赖 | **仅 Python 3 标准库** | 8+256 友好 |

## 配置 D 盘项目目录（核心）

1. 复制示例配置：

```bash
cd personal-kb
cp config.example.json config.json
```

2. 编辑 `config.json`，把 `projects.path` 改成你的真实路径，例如：

```json
{
  "roots": [
    { "id": "notes", "path": "kb", "description": "可选：跨项目随笔" },
    { "id": "projects", "path": "D:/项目", "description": "D盘项目文档（原地索引）" }
  ],
  "include_extensions": [".md", ".mdx", ".txt"],
  "exclude_dir_names": [".git", "node_modules", ".venv", "dist", "build", "__pycache__"]
}
```

路径写法建议用 `D:/项目`（正斜杠）；每个 root 的 `id` 会出现在逻辑路径前缀里，例如：

`projects/项目A/docs/需求.md`

3. 建索引并试搜：

```bash
python3 mcp/kb.py index
python3 mcp/kb.py search 需求 --root projects
python3 mcp/kb.py get projects/项目A/docs/需求说明.md
python3 mcp/kb.py stats
```

仓库里默认 `config.json` 挂了 `fixtures/fake-D-projects`，用来演示「按项目分目录、原地索引」；在你自己电脑上改成 `D:/项目` 即可。

## 快速开始（演示环境）

```bash
cd personal-kb
python3 mcp/kb.py index
python3 mcp/kb.py search 原地索引
python3 mcp/kb.py search 会议 --root projects
python3 mcp/kb.py list --root projects
```

### 接入 Cursor

1. 用 Cursor 打开本仓库  
2. 确认 `.cursor/mcp.json` 中 `personal-kb` 已启用（Customize → Tools & MCP）  
3. 问：`项目A 的需求文档里写了什么？`（Agent 应走 `kb_search` → `kb_get`）

## MCP 工具

| 工具 | 作用 |
|------|------|
| `kb_search` | 全文检索；可加 `root` 过滤（如 `projects`） |
| `kb_get` | 按逻辑路径读全文（优先读原文件） |
| `kb_list` | 按前缀 / root 列出 |
| `kb_stats` | 各 root 文档数与配置路径 |
| `kb_reindex` | 重新扫描所有 root（仍不复制） |

## 日常工作流（单次维护）

1. 文档仍写在 `D:/项目/某项目/...`  
2. 想检索时：在 Cursor 里直接问，或先 `kb.py index`  
3. 大批增删后：跑一次 `index` / `kb_reindex`（只更新索引库，不动原文）

可选习惯：下班前或 Cursor 启动后手动 index 一次；量不大时秒级完成。

## 格式说明（务实边界）

当前默认索引：`.md` / `.mdx` / `.txt`（纯文本，最稳、最省内存）。

若项目里大量是 **Word/PDF**：

- 短期：重要结论另存一份 `.md` 放在**同一项目目录**（仍不搬到知识库文件夹）  
- 中期：可再加「只读解析 docx→纯文本再进索引」的可选插件（仍原地扫描，不复制原件）

不要为了检索去维持第二份 Word 副本。

## 低配建议

- 用 `exclude_dir_names` 排除 `node_modules`、构建产物等，避免索引爆炸  
- 不要在本机跑大 embedding / 本地大模型  
- 索引库在 `data/kb.sqlite`（可 gitignore）；原文始终在 D 盘

## 验收清单

- [x] 多根目录原地索引（不复制）  
- [x] 逻辑路径 `root_id/...` + `abs_path`  
- [x] `kb_get` 优先读磁盘原文件  
- [x] 演示用 `fixtures/fake-D-projects`  
- [x] `config.example.json` 给出 `D:/项目` 写法  
