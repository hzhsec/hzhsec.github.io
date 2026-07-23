#!/usr/bin/env python3
"""快速创建新文章 - 只需输入标题和分类"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
DRAFT_DIR = SITE_ROOT / "drafts"

# 可选分类列表
CATEGORIES = [
    "Web安全", "漏洞复现", "权限提升", "应急响应", "XSS",
    "SQL注入", "SSRF", "XXE", "RCE", "文件安全",
    "工具使用", "杂项", "业务逻辑漏洞", "云上攻防",
    "内网渗透", "环境搭建", "护网", "PHP安全",
    "跨域安全", "burpsuite靶场", "top10", "移动安全",
]

def slugify(text):
    text = text.strip().lower()
    text = re.sub(r'[^\w一-鿿\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:80]

def main():
    print("=" * 50)
    print("  📝 快速创建新文章")
    print("=" * 50)

    # 输入标题
    title = input("\n📌 文章标题: ").strip()
    while not title:
        title = input("📌 文章标题（必填）: ").strip()

    # 自动生成 slug
    default_slug = slugify(title)
    slug = input(f"🔗 URL 别名 (回车默认: {default_slug}): ").strip() or default_slug

    # 选择分类
    print(f"\n📂 可选分类:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"   {i}. {cat}")
    cat_input = input(f"\n📂 分类 (输入编号或名称, 回车默认: 杂项): ").strip()
    if cat_input.isdigit() and 1 <= int(cat_input) <= len(CATEGORIES):
        category = CATEGORIES[int(cat_input) - 1]
    elif cat_input:
        category = cat_input
    else:
        category = "杂项"

    # 标签（逗号分隔）
    tags_input = input(f"🏷️  标签 (逗号分隔, 回车跳过): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    # 日期
    today = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"📅 日期 (回车默认今天 {today}): ").strip()
    date = date_input or today

    # 确认
    print(f"\n{'='*50}")
    print(f"  标题: {title}")
    print(f"  slug: {slug}")
    print(f"  分类: {category}")
    print(f"  标签: {', '.join(tags) if tags else '(无)'}")
    print(f"  日期: {date}")
    print(f"{'='*50}")
    confirm = input("\n✅ 确认创建? (Y/n): ").strip().lower()
    if confirm == "n":
        print("已取消")
        return

    # 创建文件
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    safe_slug = slugify(slug)
    filepath = DRAFT_DIR / f"{safe_slug}.md"

    if filepath.exists():
        overwrite = input(f"⚠️  {filepath.name} 已存在，覆盖? (y/N): ").strip().lower()
        if overwrite != "y":
            print("已取消")
            return

    # 生成 frontmatter
    lines = ["---"]
    lines.append(f'title: "{title}"')
    lines.append(f"slug: {slug}")
    lines.append(f'date: {date}')
    lines.append('cover: ""')
    lines.append("categories:")
    lines.append(f"  - {category}")
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {t}")
    lines.append("---")
    lines.append("")
    lines.append("")
    lines.append("<!-- 在这里写正文 -->")
    lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ 已创建: {filepath}")
    print(f"\n下一步:")
    print(f"  1. 编辑文章: notepad {filepath}")
    print(f"  2. 预览发布: cd {SITE_ROOT} && python scripts/publish_obsidian.py {filepath} --dry-run")
    print(f"  3. 正式发布: python scripts/publish_obsidian.py {filepath}")
    print(f"  4. 推送:     python scripts/publish_obsidian.py {filepath} --git-push")

if __name__ == "__main__":
    main()
