# 健康教育 HTML 与 SQL 批量导入操作说明

本文档供 Cursor Agent 执行健康教育内容生成任务时使用。目标是根据已整理的科室和健康知识标题，生成可人工审核的 HTML 文档，并生成可批量导入 MySQL 的 SQL 文件。

## 1. 输入数据

1. 科室来源：`departments.md`。
2. 健康知识标题来源：`department_health_education_titles.md`。
3. 科室总数：31 个。
4. 每个科室健康知识数量：10 条。
5. 正式批量生成前，先只生成 1 个科室样例，建议使用 `保健科`。

## 2. 输出文件

先生成样例文件，样例确认后再生成全部科室文件。

### 2.1 人工审核 HTML 文件

1. HTML 文件按科室分文件夹保存。
2. 建议目录结构：
   - `health_education_articles/保健科/health_education_articles.html`
   - 批量生成时，每个科室一个同名 HTML 文件。
3. HTML 审核文件用于人工查看内容结构和正文质量。

### 2.2 SQL 文件

1. SQL 文件名：`health_education_articles.sql`。
2. 样例阶段只包含 1 个科室的 10 条 `INSERT`。
3. 正式阶段包含 31 个科室、共 310 条 `INSERT`。

## 3. HTML 内容规范

### 3.1 数据库存储内容

`knowledge_context` 字段保存 HTML 内容块，不保存完整 HTML 页面。

不要生成：

1. `<!doctype html>`
2. `<html>`
3. `<head>`
4. `<body>`

每篇健康知识的 HTML 内容块格式如下：

```html
<link rel="stylesheet" href="/resource/css/health-education.css"><article class="health-article">...</article>
```

### 3.2 CSS 引用

1. 因系统技术限制，CSS 文件必须用 `link` 标签放在 HTML 内容块内。
2. CSS 路径固定为：`/resource/css/health-education.css`。
3. `link` 标签放在每篇 HTML 内容块开头。
4. 不要在内容块内写 JavaScript。

### 3.3 图片规则

1. 当前阶段不生成图片。
2. 后续如需加图片，图片统一放在：`/resource/imgs`。
3. 当前 HTML 中不要预留空图片标签，避免审核和展示异常。

### 3.4 文章统一模板

每篇文章必须使用统一结构：

1. 标题
2. 适用人群
3. 核心要点
4. 日常建议
5. 何时就医
6. 温馨提示

推荐 HTML 结构：

```html
<link rel="stylesheet" href="/resource/css/health-education.css"><article class="health-article"><h1>知识标题</h1><section><h2>适用人群</h2><p>...</p></section><section><h2>核心要点</h2><ul><li>...</li></ul></section><section><h2>日常建议</h2><ul><li>...</li></ul></section><section><h2>何时就医</h2><ul><li>...</li></ul></section><section><h2>温馨提示</h2><p>本文仅用于健康教育，不能替代医生面诊。如有不适，请及时到正规医疗机构就诊。</p></section></article>
```

### 3.5 免责声明

每篇文章的“温馨提示”必须包含统一免责声明：

`本文仅用于健康教育，不能替代医生面诊。如有不适，请及时到正规医疗机构就诊。`

## 4. SQL 生成规范

### 4.1 字符集

数据库、连接和表统一使用 `utf8mb4`。

SQL 文件开头必须包含：

```sql
SET NAMES utf8mb4;
START TRANSACTION;
```

SQL 文件结尾必须包含：

```sql
COMMIT;
```

### 4.2 INSERT 语句格式

每条健康知识生成一条独立 `INSERT` 语句。

固定 SQL 模板：

```sql
INSERT INTO bus_knowledge (`knowledge_name`, `knowledge_context`, `ref_property_knowledgetype`, `knowledgetype`, `dept`, `ref_property_isshow`, `isshow`, `ref_property_ispush`, `ispush`, `ref_materialtype`, `state`) VALUES ('知识标题', 'HTML正文', '11', '健康知识', '科室名称', '1', '是', '1', '阅读', '2', '0');
```

### 4.3 固定字段值

1. `ref_property_knowledgetype` 固定为 `'11'`。
2. `knowledgetype` 固定为 `'健康知识'`。
3. `ref_property_isshow` 固定为 `'1'`。
4. `isshow` 固定为 `'是'`。
5. `ref_property_ispush` 固定为 `'1'`。
6. `ispush` 固定为 `'阅读'`。
7. `ref_materialtype` 固定为 `'2'`。
8. `state` 固定为 `'0'`。

### 4.4 变量字段值

1. `knowledge_name`：取健康知识标题。
2. `knowledge_context`：取该知识对应的 HTML 内容块。
3. `dept`：取知识来源科室名称。

### 4.5 注释规则

每条 `INSERT` 前必须加一行注释，便于定位问题。

注释格式建议：

```sql
-- 保健科 - 1 - 体检报告怎么看：常见异常指标解读
INSERT INTO bus_knowledge (...) VALUES (...);
```

### 4.6 一行一条 SQL

1. 每条 `INSERT` 必须保持单行。
2. `knowledge_context` 中的换行要压缩为空格。
3. 每条注释单独一行。

### 4.7 严格转义规则

生成 SQL 前必须对变量值做严格转义：

1. 单引号 `'` 转义为 `''`。
2. 反斜杠 `\` 转义为 `\\`。
3. 换行符、回车符、制表符压缩为空格。
4. 连续空白压缩为单个空格。
5. 保留中文、中文标点和 HTML 标签。

## 5. 内容生成要求

1. 内容应面向患者和家属，语言通俗、准确、克制。
2. 每篇内容以常见健康教育需求为主，不写过度专业或少见主题。
3. 不给出具体处方剂量。
4. 不承诺疗效。
5. 不替代医生诊断和治疗。
6. 涉及急症时，要明确提醒及时就医。
7. 正式发布前，建议由对应专业科室审核。

## 6. 执行流程

### 6.1 样例阶段

1. 读取 `department_health_education_titles.md`。
2. 选择 `保健科` 的 10 条标题。
3. 为每条标题生成一篇 HTML 内容块。
4. 生成 `health_education_articles/保健科/health_education_articles.html`。
5. 生成只包含 `保健科` 10 条数据的 `health_education_articles.sql`。
6. 校验 HTML 和 SQL 格式。
7. 等待人工确认后，再生成全部 31 个科室。

### 6.2 正式批量阶段

1. 读取全部 31 个科室、310 条标题。
2. 为每条标题生成 HTML 内容块。
3. 每个科室生成一个 HTML 审核文件。
4. 生成统一的 `health_education_articles.sql`。
5. SQL 文件使用 `SET NAMES utf8mb4;`、`START TRANSACTION;` 和 `COMMIT;`。
6. 校验每个科室正好 10 条，合计 310 条。

## 7. 交付前校验清单

1. 是否只生成了约定范围内的科室。
2. 每个科室是否正好 10 条。
3. HTML 内容是否只包含内容块，不包含完整页面结构。
4. 每篇 HTML 是否包含 CSS `link`。
5. CSS 路径是否为 `/resource/css/health-education.css`。
6. 是否未生成图片标签。
7. 每篇是否包含统一免责声明。
8. SQL 是否以 `SET NAMES utf8mb4;` 开头。
9. SQL 是否包含 `START TRANSACTION;` 和 `COMMIT;`。
10. 每条 SQL 前是否有注释。
11. 每条 `INSERT` 是否单独一行。
12. SQL 变量值是否完成严格转义。
13. `dept` 是否与科室名称完全一致。
14. `knowledge_name` 是否与标题完全一致。
15. 固定字段值是否与模板一致。

## 8. 当前推荐下一步

下一步只生成 `保健科` 样例，不直接生成 31 个科室的正式批量文件。样例经人工确认后，再执行正式批量生成。
