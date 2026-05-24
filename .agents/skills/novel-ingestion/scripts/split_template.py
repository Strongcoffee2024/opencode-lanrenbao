#!/usr/bin/env python3
"""小说按章节分割模板 v2.0
支持 .docx 和 .txt 格式。

用法:
  1. 修改 SRC 为源文件路径
  2. 修改 CHAPTER_RE 匹配章节标题格式
  3. 运行: python split_template.py

分割文件输出到 workspace/<文件名>_分割/
"""
import sys, os, re, glob
sys.stdout.reconfigure(encoding='utf-8')


# ====== 配置区 ======
SRC = r'D:\Vaul\raw\01-Writing material\<替换为小说文件名>.docx'
# ===================


# 章节正则（按实际格式调整）
# 我吃西红柿系列：第一集 XXX 第一章 XXXX
CHAPTER_RE = re.compile(
    r'^(第[一二三四五六七八九十百千\d]+集\s+\S+\s+第[一二三四五六七八九十百千\d]+章\s+.+)$'
)
# 普通章节：第一章 XXXX
# CHAPTER_RE = re.compile(r'^(第[一二三四五六七八九十百千\d]+章\s+.+)$')


def clean_filename(title: str) -> str:
    """清理标题中的特殊字符，生成安全的文件名"""
    safe = title.replace(' ', '_').replace('（', '_').replace('）', '_')
    safe = safe.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe = safe.replace('"', '_').replace("'", '_').replace('`', '_')
    safe = re.sub(r'[^\w_\u4e00-\u9fff]', '', safe)
    return safe


def extract_text(path: str) -> str:
    """根据文件扩展名提取文本"""
    ext = os.path.splitext(path)[1].lower()
    print(f'检测到文件格式: {ext}', file=sys.stderr)

    if ext == '.docx':
        try:
            from docx import Document
        except ImportError:
            print('需要 python-docx: pip install python-docx', file=sys.stderr)
            sys.exit(1)
        doc = Document(path)
        return '\n'.join([p.text for p in doc.paragraphs])

    elif ext == '.txt':
        with open(path, 'rb') as f:
            raw = f.read()
        for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                text = raw.decode(enc, errors='ignore')
                print(f'解码成功: {enc}', file=sys.stderr)
                return text
            except UnicodeDecodeError:
                continue
        print('错误：无法解码文件，请检查编码', file=sys.stderr)
        sys.exit(1)

    else:
        print(f'错误：不支持的文件格式 {ext}', file=sys.stderr)
        sys.exit(1)


def split_chapters(text: str) -> list[tuple[str, str]]:
    """按章节标题分割文本，返回 [(标题, 内容), ...]"""
    lines = text.split('\n')
    chapters = []

    for i, line in enumerate(lines):
        line_s = line.strip()
        if CHAPTER_RE.match(line_s):
            if chapters:
                # 把前面的行追加到上一个章节
                prev_content = '\n'.join(lines[prev_start:i])
                while prev_content and not prev_content[-1].strip():
                    prev_content = prev_content[:-1]
                chapters[-1] = (chapters[-1][0], prev_content)
            chapters.append((line_s, ''))
            prev_start = i

    # 最后一章
    if chapters:
        last_content = '\n'.join(lines[prev_start:])
        while last_content and not last_content[-1].strip():
            last_content = last_content[:-1]
        chapters[-1] = (chapters[-1][0], last_content)

    return chapters


def main():
    if not os.path.exists(SRC):
        print(f'错误：文件不存在 {SRC}', file=sys.stderr)
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(SRC))[0]
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SRC)))),
                           'workspace', f'{base_name}_分割')

    # === 检查是否已分割 ===
    if os.path.exists(out_dir):
        existing = [f for f in os.listdir(out_dir) if f.endswith('.md')]
        if existing:
            print(f'分割文件已存在：{out_dir}（{len(existing)} 个文件）', file=sys.stderr)
            ans = input('重新分割？(y/N): ').strip().lower()
            if ans != 'y':
                print('跳过分割', file=sys.stderr)
                return

    text = extract_text(SRC)
    chapters = split_chapters(text)

    total = len(chapters)
    if total == 0:
        print('错误：未找到任何章节！请检查 CHAPTER_RE 正则', file=sys.stderr)
        sys.exit(1)

    print(f'共发现 {total} 章', file=sys.stderr)
    os.makedirs(out_dir, exist_ok=True)

    for idx, (title, content) in enumerate(chapters, 1):
        fname = f'{base_name}_{idx:03d}_{clean_filename(title)}.md'
        fpath = os.path.join(out_dir, fname)
        with open(fpath, 'w', encoding='utf-8') as fout:
            fout.write(f'# {title}\n\n{content}\n')
        print(f'[{idx}/{total}] {fname}', file=sys.stderr)

    print(f'\n✅ 分割完成！共 {total} 章输出到 {out_dir}', file=sys.stderr)


if __name__ == '__main__':
    main()
