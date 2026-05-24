---
name: novel-ingestion
description: 长篇小说逐章摄入工作流。处理 raw/ 中的小说文件（.docx / .txt GBK），分割为章节，生成写作技巧分析类 wiki 文章到 wiki/10-写作素材/。一次只处理一章，处理完询问用户是否继续。触发词：摄入小说、处理小说、继续摄入、继续星辰变、继续寸芒。
---

# 小说摄入工作流 (Novel Ingestion) v2.0

## 核心原则

1. **文件类型检测优先**：检查实际扩展名，不假设 .txt
2. **单一进度源**：一切以 `context/active.md` 为准
3. **分割是一次性的，摄入是逐章的**：分割可批量，摄入每章间必须询问
4. **深度优先于速度**：每章做到写作技巧+可复用模式+例证，宁少勿滥

---

## 阶段 0：快速恢复

用户说「继续」或「继续摄入」：

1. 读 `context/active.md` → 找到对应小说的进度
2. 从已处理列表末尾确认最后一章
3. 从 `workspace/<小说名>_分割/` 取下一个编号的文件
4. 跳至**阶段 3：逐章摄入**

⚠️ **不要重新扫描 raw/，不要重复分割，不要查 `raw/` 下的冗余进度文件**

---

## 阶段 1：文件检测与分割（仅新小说）

### 1.1 检测文件

```python
path = 'raw/01-Writing material/<文件名>'
ext = os.path.splitext(path)[1].lower()

if ext == '.docx':
    from docx import Document
    doc = Document(path)
    text = '\n'.join([p.text for p in doc.paragraphs])
elif ext == '.txt':
    with open(path, 'rb') as f:
        raw = f.read()
    try: text = raw.decode('utf-8')
    except: text = raw.decode('gbk', errors='ignore')
```

### 1.2 分割

**先用 glob 检查分割目录是否存在且非空**，存在则跳过。

章节正则（以我吃西红柿小说为例）：
```python
CHAPTER_RE = re.compile(
    r'^(第[一二三四五六七八九十百千\d]+集\s+\S+\s+第[一二三四五六七八九十百千\d]+章\s+.+)$'
)
```

按标题行分割，输出到 `workspace/<文件名>_分割/`。
命名格式：`<文件名>_{序号:03d}_{清理后的标题}.md`
清理：`re.sub(r'[^\w_\u4e00-\u9fff]', '', title.replace(' ', '_'))`

---

## 阶段 2：初始化进度（仅新小说）

写入 `context/active.md`：

```markdown
## <小说名> 摄入进度
- 原始文件：raw/01-Writing material/<文件名>
- 分割数量：<N> 章
- 已处理：[无]
- 待处理：[001 ... 共 N 章]
- 当前状态：等待用户确认
- 最后更新：YYYY-MM-DD
```

⚠️ **不创建 `raw/XX_摄入进度.md`。进度只写 context/active.md。**

---

## 阶段 3：逐章摄入（核心循环）

### 每章处理步骤（一次一章）：

#### 3.1 读取分割文件
`workspace/<小说名>_分割/<文件名>` — 按编号顺序读取

#### 3.2 内容分析
- **核心概念**：一句话总结本章功能（不是剧情摘要）
- **写作技巧**：心理描写、战斗设计、悬念设置、节奏控制等
- **可复用模式**：能迁移到其他创作的模板（附原文示例）
- **伏笔/回收**：留意前后章节的呼应关系

#### 3.3 写入 Wiki 文章

路径：`wiki/10-写作素材/<小说名>_<序号>_<标题>.md`

格式标准：
```markdown
---
created: YYYY-MM-DD
source: raw/01-Writing material/<小说名>.<ext>
tags: [小说写作, 玄幻, <小说名>, #Anki]
---

# 章节标题

## 核心概念
> 一句话

## 详细分析
- 标注原文片段 + 写作技巧提炼
- 用表格对比、模式提取、技巧归类

## 可复用模式
### 模式 N：名称
```[模板]```

## 写作技巧小结
> 本章最值得学的 1-2 个点

## 相关链接
- [[上一章]]
- [[下一章]]

## 来源
- [[raw/01-Writing material/<小说名>.<ext>]]
```

#### 3.4 更新相关文件
- `wiki/index.md` → 追加 `- [[10-写作素材/<文件名>]]`
- `context/active.md` → 更新已处理范围

#### 3.5 暂停，询问用户
```
是否继续处理下一章「<标题>」？
→ 继续 → 回到 3.1
→ 停止 → 结束
```

---

## 编码提醒（仅 .txt）
```python
for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
    try:
        text = raw.decode(enc, errors='ignore')
        if '章节关键字' in text: break
    except: pass
```

## PowerShell 限制
- 不要用 heredoc
- 不要用单行命令处理 GBK/中文
- 必须用 Python 处理文件 I/O

## 相关脚本
- 分割模板：`.agents/skills/novel-ingestion/scripts/split_template.py`
