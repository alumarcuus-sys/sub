#!/usr/bin/env python3
"""
简单的 ASS 拼写与术语检查工具（用作 GitHub Actions 的提醒脚本）。
用法示例：git diff ... | python tools/check_ass_spelling.py --diff

输出：生成 ass_spell_comment.md 并通过 GitHub Actions 命令设置 outputs.count
"""
import sys
import re
from collections import defaultdict

# 简单的词典：常见错别字或术语不一致 -> 建议写法
DICT = {
    '字幕组': '字幕组',
    '翻译家': '翻译组',
    '尤利': '由里',
    'subtitile': 'subtitle',
    'teh': 'the',
}

MARKER = '<!-- ass-spell-check -->'

def read_stdin():
    return sys.stdin.read()

def parse_added_lines(diff_text):
    # 如果输入看起来像是完整文件（不含 diff 前缀），则直接返回所有行；
    # 否则提取以 + 开头的新增内容行（忽略 diff 元信息）。
    lines = diff_text.splitlines()
    if lines and not any(l.startswith("+") for l in lines):
        return lines
    added = []
    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            added.append(line[1:])
    return added

def check_lines(lines):
    issues = defaultdict(list)
    for i, line in enumerate(lines, 1):
        for wrong, right in DICT.items():
            if wrong in line:
                issues[wrong].append((i, line.strip()))
    return issues

def main():
    text = read_stdin()
    if not text.strip():
        # 没有 diff 输入时，也可尝试读取文件路径参数（跳过复杂实现）
        print('::set-output name=count::0')
        return
    added = parse_added_lines(text)
    issues = check_lines(added)
    total = sum(len(v) for v in issues.values())

    if total == 0:
        print('::set-output name=count::0')
        return

    with open('ass_spell_comment.md', 'w', encoding='utf-8') as f:
        f.write(MARKER + "\n")
        f.write(f"检测到 {total} 处可能的问题。\n\n")
        for wrong, occurrences in issues.items():
            f.write(f"- 建议将 “{wrong}” 改为 “{DICT[wrong]}” ，出现 {len(occurrences)} 次。\n")
            for ln, content in occurrences:
                f.write(f"  - 示例：{content}\n")
        f.write('\n请人工确认并在需要时修正。')

    # 输出 GH Actions 输出变量（旧式命令），以便 workflow 的后续 step 读取
    print(f'::set-output name=count::{total}')

if __name__ == '__main__':
    main()
