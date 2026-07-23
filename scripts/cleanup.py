#!/usr/bin/env python3
"""按照用户要求整理站点结构"""
import json, shutil, os, re
from pathlib import Path

SITE_ROOT = Path("F:/hugo/hzhsec.github.io")
STATE_FILE = SITE_ROOT / "scripts" / "site_state.json"

def load():
    return json.loads(STATE_FILE.read_text("utf-8"))

def save(s):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), "utf-8")

state = load()
posts = state["posts"]
removed_slugs = set()
changed = 0

# === 1. 删除 XSS, Web安全, XXE 目录 ===
delete_cats = ["XSS", "Web安全", "XXE"]
print("=== 1. 删除分类: XSS, Web安全, XXE ===")
for p in list(posts):
    cats = p.get("categories", [])
    if any(c in delete_cats for c in cats):
        removed_slugs.add(p["slug"])
        posts.remove(p)
        print(f"  🗑️ {p.get('title','')}")
print(f"  共删除 {len([p for p in posts if p.get('slug') in removed_slugs and any(c in delete_cats for c in p.get('categories',[]))])} 篇")

# === 2. 权限提升整理：按linux/windows分类 ===
print("\n=== 2. 权限提升整理 ===")
linux_slugs = []
windows_slugs = []
for p in posts:
    if "权限提升" not in p.get("categories", []):
        continue
    title = p.get("title", "")
    slug = p["slug"]
    if any(k in title for k in ["Linux", "linux", "Dirty", "SUID", "SUDO", "NFS", "PATH", "Cron", "LXD", "Docker", "Rbash", "内核"]):
        linux_slugs.append(slug)
        p["categories"] = ["权限提升"]
    elif any(k in title for k in ["Windows", "windows", "UAC", "DLL"]):
        windows_slugs.append(slug)
        p["categories"] = ["权限提升"]
    else:
        p["categories"] = ["权限提升"]

print(f"  Linux: {len(linux_slugs)} 篇")
print(f"  Windows: {len(windows_slugs)} 篇")

# === 3. 删除 top10 和 漏洞复现 ===
print("\n=== 3. 删除 top10, 漏洞复现 ===")
delete_cats2 = ["top10", "漏洞复现"]
for p in list(posts):
    cats = p.get("categories", [])
    if any(c in delete_cats2 for c in cats):
        removed_slugs.add(p["slug"])
        posts.remove(p)
        print(f"  🗑️ [{p.get('categories',[])}] {p.get('title','')}")
print(f"  共删除...")

# === 4. 去序号 ===
print("\n=== 4. 去掉标题序号 ===")
for p in posts:
    title = p.get("title", "")
    new_title = re.sub(r'^[\d]+[.．、）\)]\s*', '', title)
    new_title = re.sub(r'^[（(]\d+[)）]\s*', '', new_title)
    if new_title != title:
        print(f"  {title} → {new_title}")
        p["title"] = new_title
        changed += 1
print(f"  修改了 {changed} 个标题")

# === 5. 杂项去重 ===
# 只有一个杂项，但有些文章可能重复在不同分类
# 只保留 slug 唯一的
print("\n=== 5. 去重 ===")
seen = set()
dup_count = 0
for p in list(posts):
    slug = p["slug"]
    if slug in seen:
        posts.remove(p)
        dup_count += 1
        print(f"  🗑️ 重复: {p.get('title','')}")
    else:
        seen.add(slug)
print(f"  删除 {dup_count} 篇重复文章")

# === 保存 ===
save(state)

# === 删除对应的 HTML 目录 ===
print("\n=== 清理生成的 HTML 目录 ===")
for slug in removed_slugs:
    for d in SITE_ROOT.glob(f"list/*/{slug}"):
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)

# 删除空分类目录
for d in SITE_ROOT.glob("list/*"):
    if d.is_dir() and d.name not in ["page"]:
        has_content = len(list(d.glob("*/index.html"))) > 0
        if not has_content and d.name != "page":
            shutil.rmtree(d, ignore_errors=True)
            print(f"  🗑️ 空目录: {d.name}")

print("\n✅ 完成")
