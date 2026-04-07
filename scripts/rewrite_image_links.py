#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""批量将文章中的图片引用改写为指定 CDN 地址格式。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable


DEFAULT_BASE_URL = "https://cdn.jsdmirror.com/gh/hzhsec/upload@main"
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown"}
HTML_EXTENSIONS = {".html", ".htm"}

# 匹配 Markdown 图片语法：![alt](path "title")
MARKDOWN_IMAGE_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\((?P<path><[^>]+>|[^)]+?)(?:\s+"[^"]*")?\)'
)

# 匹配 HTML img 标签中的 src 属性。
HTML_IMAGE_RE = re.compile(
    r'<img\b(?P<before>[^>]*?)\bsrc=(?P<quote>[\'\"])(?P<src>.*?)(?P=quote)(?P<after>[^>]*?)>',
    re.IGNORECASE,
)


def is_remote_path(path: str) -> bool:
    """判断是否为无需改写的远程或内嵌资源。"""
    lowered = path.lower()
    return lowered.startswith(("http://", "https://", "data:", "mailto:"))


def extract_filename(path: str) -> str:
    """从路径中提取文件名，并去掉查询串和锚点。"""
    cleaned = path.strip().strip("<>").split("?", 1)[0].split("#", 1)[0]
    cleaned = cleaned.replace("\\", "/").rstrip("/")
    return Path(cleaned).name


def build_cdn_url(base_url: str, filename: str) -> str:
    """拼接目标 CDN 地址。"""
    return f"{base_url.rstrip('/')}/{filename}"


def replace_markdown_images(content: str, base_url: str) -> tuple[str, int]:
    """替换 Markdown 图片引用。"""
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        original_path = match.group("path").strip()
        if is_remote_path(original_path.strip("<>")):
            return match.group(0)

        filename = extract_filename(original_path)
        if not filename:
            return match.group(0)

        count += 1
        new_url = build_cdn_url(base_url, filename)
        return f"![{filename}]({new_url})"

    return MARKDOWN_IMAGE_RE.sub(_replace, content), count


def replace_html_images(content: str, base_url: str) -> tuple[str, int]:
    """仅替换 HTML img 标签的 src，保留原标签结构。"""
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        original_src = match.group("src").strip()
        if is_remote_path(original_src):
            return match.group(0)

        filename = extract_filename(original_src)
        if not filename:
            return match.group(0)

        count += 1
        new_url = build_cdn_url(base_url, filename)
        before = match.group("before")
        after = match.group("after")
        quote = match.group("quote")
        return f"<img{before}src={quote}{new_url}{quote}{after}>"

    return HTML_IMAGE_RE.sub(_replace, content), count


def repair_markdown_images_in_html(content: str) -> tuple[str, int]:
    """把误写进 HTML 的 Markdown 图片语法修正回 img 标签。"""
    count = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal count
        path = match.group("path").strip()
        if not is_remote_path(path.strip("<>")):
            return match.group(0)

        alt = match.group("alt").strip() or extract_filename(path)
        url = path.strip("<>")
        count += 1
        return f'<img src="{url}" alt="{alt}">'

    return MARKDOWN_IMAGE_RE.sub(_replace, content), count


def iter_target_files(paths: Iterable[str], include_html: bool) -> Iterable[Path]:
    """遍历需要处理的文件。"""
    seen: set[Path] = set()
    suffixes = set(MARKDOWN_EXTENSIONS)
    if include_html:
        suffixes.update(HTML_EXTENSIONS)

    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if path.is_file() and path.suffix.lower() in suffixes:
            if path not in seen:
                seen.add(path)
                yield path
            continue

        if path.is_dir():
            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in suffixes:
                    continue
                if file_path in seen:
                    continue
                seen.add(file_path)
                yield file_path


def process_file(file_path: Path, base_url: str, include_html: bool, dry_run: bool) -> int:
    """处理单个文件并返回替换数量。"""
    try:
        original_content = file_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"跳过读取失败文件: {file_path} ({error})")
        return 0

    updated_content = original_content
    total_count = 0
    suffix = file_path.suffix.lower()

    if suffix in MARKDOWN_EXTENSIONS:
        updated_content, markdown_count = replace_markdown_images(updated_content, base_url)
        total_count += markdown_count

    if include_html and suffix in HTML_EXTENSIONS:
        updated_content, repair_count = repair_markdown_images_in_html(updated_content)
        updated_content, html_count = replace_html_images(updated_content, base_url)
        total_count += repair_count + html_count

    if total_count and not dry_run and updated_content != original_content:
        try:
            with file_path.open("w", encoding="utf-8", newline="") as file:
                file.write(updated_content)
        except OSError as error:
            print(f"跳过写入失败文件: {file_path} ({error})")
            return 0

    return total_count


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数。"""
    parser = argparse.ArgumentParser(
        description="批量将文章中的图片引用改写为指定 CDN 地址格式。"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="要处理的文件或目录，默认当前目录。",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"CDN 地址前缀，默认：{DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--include-html",
        action="store_true",
        help="同时处理 .html 文件，并仅替换 <img> 标签中的 src。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览替换结果，不写回文件。",
    )
    return parser


def main() -> int:
    """程序入口。"""
    parser = build_parser()
    args = parser.parse_args()

    total_files = 0
    changed_files = 0
    total_replacements = 0

    for file_path in iter_target_files(args.paths, args.include_html):
        total_files += 1
        replacements = process_file(file_path, args.base_url, args.include_html, args.dry_run)
        if replacements:
            changed_files += 1
            total_replacements += replacements
            action = "预览" if args.dry_run else "已处理"
            print(f"{action}: {file_path} ({replacements} 处)")

    action = "预览完成" if args.dry_run else "处理完成"
    print(
        f"{action}，共扫描 {total_files} 个文件，修改 {changed_files} 个文件，替换 {total_replacements} 处图片引用。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
