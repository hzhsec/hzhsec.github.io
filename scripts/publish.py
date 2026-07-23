#!/usr/bin/env python3
"""📝 一键发布文章 - 全流程交互

直接写正文，不用写 frontmatter，运行后会一步步引导你完成发布。

用法:
    python scripts/publish.py 文章.md              # 交互式全流程
    python scripts/publish.py 文章.md --dry-run    # 只看预览
    python scripts/publish.py 文章.md --git-push   # 跳过询问直接推
"""

import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

SITE_ROOT = Path(__file__).resolve().parent.parent
PUBLISH_SCRIPT = SITE_ROOT / "scripts" / "publish_obsidian.py"
CONFIG_FILE = SITE_ROOT / "scripts" / ".publish_config.json"

CATEGORIES = [
    "Web安全", "漏洞复现", "权限提升", "应急响应", "XSS",
    "SQL注入", "SSRF", "XXE", "RCE", "文件安全",
    "工具使用", "杂项", "业务逻辑漏洞", "云上攻防",
    "内网渗透", "环境搭建", "护网", "PHP安全", "跨域安全",
    "burpsuite靶场", "top10", "移动安全",
]


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text("utf-8"))
    return {}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")


def slugify(text):
    text = re.sub(r'[^\w一-鿿\s-]', '', text.strip().lower())
    text = re.sub(r'[\s_]+', '-', text).strip("-")
    return text[:80]


def ask(prompt, default=None):
    hint = f" [{default}]" if default else ""
    val = input(f"{prompt}{hint}: ").strip()
    return val if val else (default or "")


def pick(prompt, items):
    print(f"\n{prompt}")
    for i, v in enumerate(items, 1):
        print(f"  {i}. {v}")
    while True:
        r = input(f"编号 (1-{len(items)}, 或直接输入): ").strip()
        if r.isdigit() and 1 <= int(r) <= len(items):
            return items[int(r) - 1]
        if r:
            return r


def yesno(prompt, default=True):
    hint = " [Y/n]" if default else " [y/N]"
    r = input(f"{prompt}{hint}: ").strip().lower()
    if not r:
        return default
    return r in ("y", "yes", "是")


def add_frontmatter(filepath):
    """如果没有 frontmatter，交互式添加"""
    raw = filepath.read_text("utf-8")
    if re.match(r"^---\s*\n.*?\n---\s*\n?", raw, re.DOTALL):
        return True  # 已有，跳过

    title_m = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
    cfg = load_config()
    last_cat = cfg.get("last_category", "")
    last_tags = cfg.get("last_tags", [])

    print(f"\n{'='*50}")
    print(f"  📝 {filepath.name}")
    print(f"{'='*50}")

    title = ask("📌 标题", title_m.group(1).strip() if title_m else filepath.stem)
    slug = ask("🔗 链接别名", slugify(title))
    cat = pick("📂 分类", CATEGORIES)
    cfg["last_category"] = cat
    tags_raw = ask("🏷️  标签(逗号分隔)", ", ".join(last_tags))
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    if tags:
        cfg["last_tags"] = tags
    date = ask("📅 日期", datetime.now().strftime("%Y-%m-%d"))
    save_config(cfg)

    fm = ["---"]
    fm.append(f'title: "{title}"')
    fm.append(f"slug: {slug}")
    fm.append(f"date: {date}")
    fm.append('cover: ""')
    fm.append("categories:")
    fm.append(f"  - {cat}")
    if tags:
        fm.append("tags:")
        for t in tags:
            fm.append(f"  - {t}")
    fm.append("---")
    filepath.write_text("\n".join(fm) + "\n\n" + raw, "utf-8")
    print("  ✅ 元信息已添加")
    return True


def main():
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        return

    # 分离参数
    file_args, other_args = [], []
    for a in args:
        (other_args if a.startswith("-") else file_args).append(a)

    if not file_args:
        print("[-] 请指定 Markdown 文件")
        return

    dry_run = "--dry-run" in other_args
    auto_push = "--git-push" in other_args

    # 处理每个文件
    for fp in file_args:
        path = Path(fp)
        if not path.exists():
            print(f"[-] 不存在: {path}")
            continue
        if path.suffix.lower() not in (".md", ".markdown"):
            continue
        add_frontmatter(path)

        if not dry_run and not auto_push:
            print()
            if not yesno("🔍 预览?", True):
                continue
            r = subprocess.run([sys.executable, str(PUBLISH_SCRIPT), str(path), "--dry-run"])
            if r.returncode != 0:
                continue
            if not yesno("\n📦 发布到本地?", True):
                continue
            subprocess.run([sys.executable, str(PUBLISH_SCRIPT), str(path)])
            if yesno("\n🌍 推送到 GitHub?", False):
                subprocess.run([sys.executable, str(PUBLISH_SCRIPT), str(path), "--git-push"])
        elif dry_run:
            subprocess.run([sys.executable, str(PUBLISH_SCRIPT), str(path), "--dry-run"] + [a for a in other_args if a != "--dry-run"])
        else:
            subprocess.run([sys.executable, str(PUBLISH_SCRIPT), str(path)] + other_args)


if __name__ == "__main__":
    main()
