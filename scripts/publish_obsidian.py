#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import html
import json
import math
import os
import sys
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import yaml
from bs4 import BeautifulSoup
from jinja2 import Environment

DEFAULT_SITE_ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://hzhsec.github.io"
SITE_TITLE = "Hzhsec home"
SITE_AUTHOR = "hzhsec"
SITE_DESCRIPTION = "Ladder@"
STATE_FILE = "site_state.json"
INTRO_TITLE = "hzhsec"
INTRO_SUBTITLE = "阅读｜思考｜产出｜进步"
INTRO_TEXT = "从未停止对未知的探索,一切始于热爱"
AVATAR = "https://cdn.jsdmirror.com/gh/hzhsec/upload@main/hzhsec.png"
HOME_POST_LIMIT = 4
TOC_MAX_LEVEL = 3
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
INVALID_SEGMENT = re.compile(r'[<>:"/\\|?*]+')
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ORDERED_RE = re.compile(r"^\d+\.\s+(.*)$")
UNORDERED_RE = re.compile(r"^[-*+]\s+(.*)$")
IMAGE_RE = re.compile(r"!\[(.*?)\]\((.*?)(?:\s+\".*?\")?\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
ENV = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
BASE = ENV.from_string("""<!DOCTYPE html>
<html lang=\"en\"><head>
<link rel=\"stylesheet\" href=\"/css/custom.css\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>{{ title }}</title><meta charset=\"utf-8\"><meta name=\"description\" content=\"{{ desc }}\"><meta name=\"author\" content=\"hzhsec\">
<link rel=\"canonical\" href=\"{{ canonical }}\"><meta property=\"og:title\" content=\"{{ title }}\" /><meta property=\"og:description\" content=\"{{ og_desc }}\" />
<meta property=\"og:type\" content=\"{{ og_type }}\" /><meta property=\"og:url\" content=\"{{ canonical }}\" />
{% if published %}<meta property=\"article:section\" content=\"list\" /><meta property=\"article:published_time\" content=\"{{ published }}\" /><meta property=\"article:modified_time\" content=\"{{ published }}\" />{% endif %}
<meta name=\"twitter:card\" content=\"summary\"/><meta name=\"twitter:title\" content=\"{{ title }}\"/><meta name=\"twitter:description\" content=\"{{ og_desc }}\"/>
<link rel=\"icon\" href=\"/static/hzhsec.png\" sizes=\"16x16\"><link rel=\"apple-touch-icon\" href=\"/static/hzhsec.png\"><link rel=\"manifest\" href=\"/static/hzhsec.png\">
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/style.css\" />
<link rel=\"stylesheet\" href=\"/css/main.min.ec28f09e946fc0df77c187fcd0d0ebde58fca6de8efb8e1620f3d45c32d4da88.css\" crossorigin=\"anonymous\" media=\"screen\" />
<link rel=\"stylesheet\" href=\"/scss/highlight/github-dark.min.min.66034289ee9a113219a2c4aae0a8bd2095ab255c832a42efcf5863f10814e7a1.css\" />
<script src=\"/js/highlight.min.min.c098d85b5396dec4707ea2cead1445b4dc2ff0fc56b8dbbd9049d0d1c50ad237.js\"></script><script>hljs.highlightAll();</script>
<script>(()=>{var t=window.matchMedia&&window.matchMedia(\"(prefers-color-scheme: dark)\").matches,e=localStorage.getItem(\"theme\");t&&e===null&&(localStorage.setItem(\"theme\",\"dark\"),document.documentElement.setAttribute(\"data-dark-mode\",\"\")),t&&e===\"dark\"&&document.documentElement.setAttribute(\"data-dark-mode\",\"\"),e===\"dark\"&&document.documentElement.setAttribute(\"data-dark-mode\",\"\")})()</script></head>
<body><main class=\"wrapper\"><nav class=\"navigation\"><section class=\"container\"><a class=\"navigation-brand\" href=\"/\">主页</a><input type=\"checkbox\" id=\"menu-toggle\" />
<label class=\"menu-button float-right\" for=\"menu-toggle\"><span></span><span></span><span></span></label><ul class=\"navigation-list\" id=\"navigation-list\">
<li class=\"navigation-item navigation-menu\"><a class=\"navigation-link\" href=\"/list/\">目录</a></li><li class=\"navigation-item navigation-menu\"><a class=\"navigation-link\" href=\"/archives/\">归档</a></li>
<li class=\"navigation-item navigation-menu\"><a class=\"navigation-link\" href=\"/message/\">关于</a></li><li class=\"navigation-item navigation-menu\"><a class=\"navigation-link\" href=\"/categories/\">分类</a></li>
<li class=\"navigation-item navigation-menu\"><a class=\"navigation-link\" href=\"https://umami-evtq.vercel.app/share/NdRAzdY1AwLB5KF2/hzhsec.github.io\">网站统计</a></li><li class=\"navigation-item menu-separator\"><span>|</span></li>
<li class=\"navigation-item navigation-social\"><a class=\"navigation-link\" href=\"https://github.com/hzhsec\">GitHub</a></li><li class=\"navigation-item navigation-social\"><a class=\"navigation-link\" href=\"/message/\">Mail</a></li></ul></section></nav>
<div id=\"content\">{{ content }}</div><footer class=\"footer\"><p>&copy; {{ year }} <a href=\"{{ site_url }}/\">{{ site_title }}</a> Powered by <a href=\"https://gohugo.io/\" rel=\"noopener\" target=\"_blank\">Hugo️️</a> <a href=\"https://github.com/guangzhengli/hugo-theme-ladder\" rel=\"noopener\" target=\"_blank\">Ladder</a></p></footer>
<a href=\"#top\" class=\"top-link\" id=\"top-link\" accesskey=\"g\">Top</a><script>var mybutton=document.getElementById(\"top-link\");window.onscroll=function(){if(document.body.scrollTop>800||document.documentElement.scrollTop>800){mybutton.style.visibility=\"visible\";mybutton.style.opacity=\"1\";}else{mybutton.style.visibility=\"hidden\";mybutton.style.opacity=\"0\";}};</script>
<script>document.querySelectorAll('pre > code').forEach((codeblock)=>{const copybutton=document.createElement('button');copybutton.classList.add('copy-code');copybutton.innerHTML='Copy';function done(){copybutton.innerHTML='Copied';setTimeout(()=>{copybutton.innerHTML='Copy';},2000);}copybutton.addEventListener('click',()=>{if('clipboard' in navigator){navigator.clipboard.writeText(codeblock.textContent);done();return;}const range=document.createRange();range.selectNodeContents(codeblock);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);try{document.execCommand('copy');done();}catch(e){}selection.removeRange(range);});codeblock.parentNode.appendChild(copybutton);});</script></main></body>
<script src=\"/main.min.6bb26b69159420159c74dc9e097b06a578ed2b68c701466a91a44a9632d851bd0af167a1b30012387b4c512b48ad9ad4d3394e04d77ae38d57e1920fe4ed34fe.js\" crossorigin=\"anonymous\" defer></script></html>""")

@dataclass
class SectionInfo:
    slug: str
    title: str
    parent: str
    order: int = 0

@dataclass
class PostRecord:
    slug: str
    title: str
    source_note: str
    summary: str
    date_iso: str
    word_count: int
    reading_minutes: int
    rel_permalink: str
    section_path: list[str]
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    featured: bool = False
    body_html: str = ""
    toc_html: str = ""
    article_body_text: str = ""


def configure_windows_console() -> None:
    """?? Windows ????? UTF-8 ???"""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def is_publishable_post(post: PostRecord) -> bool:
    """??????????????????"""
    if post.slug in {"__index", "__index__"}:
        return False
    if "/__index" in post.rel_permalink:
        return False
    if not post.title.strip():
        return False
    return True

def sanitize_segment(value: str) -> str:
    value = INVALID_SEGMENT.sub("-", value.strip()).rstrip(". ").strip()
    return value or "post"

def taxonomy_slug(name: str) -> str:
    return sanitize_segment(name).replace(" ", "-")

def quote_path(path: str) -> str:
    return "/".join(quote(part) for part in path.strip("/").split("/"))

def abs_url(path: str) -> str:
    return f"{SITE_URL}/{quote_path(path).strip('/')}/" if path else f"{SITE_URL}/"

def normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()

def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,|]", value) if item.strip()]
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    return [normalize_text(value)]

def parse_date(value: Any) -> dt.datetime:
    tz = dt.timezone(dt.timedelta(hours=8))
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=tz)
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time(10, 0), tzinfo=tz)
    text = normalize_text(value)
    if not text:
        return dt.datetime.now(tz)
    for pattern in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d"]:
        try:
            parsed = dt.datetime.strptime(text, pattern)
            if "H" not in pattern:
                parsed = parsed.replace(hour=10, minute=0, second=0)
            return parsed.replace(tzinfo=tz)
        except ValueError:
            pass
    parsed = dt.datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=tz)

def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    text = text.lstrip("\ufeff")
    match = FM_RE.match(text)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, text[match.end():]

def render_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = CODE_RE.sub(lambda m: f"<code>{html.escape(m.group(1))}</code>", text)
    text = IMAGE_RE.sub(lambda m: f'<img src="{html.escape(m.group(2).strip())}" alt="{html.escape(m.group(1).strip() or Path(m.group(2).strip()).name)}">', text)
    text = LINK_RE.sub(lambda m: f'<a href="{html.escape(m.group(2).strip())}">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = ITALIC_RE.sub(r"<em>\1</em>", text)
    return text

def slugify_heading(text: str, used: set[str]) -> str:
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff\-_ ]+", "", text).strip().lower().replace(" ", "-") or "section"
    candidate = text
    index = 2
    while candidate in used:
        candidate = f"{text}-{index}"
        index += 1
    used.add(candidate)
    return candidate

def build_toc(headings: list[tuple[int, str, str]]) -> str:
    filtered = [(level, hid, title) for level, hid, title in headings if level <= TOC_MAX_LEVEL]
    if not filtered:
        return ""

    # ????????????????????????
    root: list[dict[str, Any]] = []
    stack: list[tuple[int, list[dict[str, Any]]]] = [(0, root)]
    for level, hid, title in filtered:
        while stack and level <= stack[-1][0]:
            stack.pop()
        node = {"hid": hid, "title": title, "children": []}
        stack[-1][1].append(node)
        stack.append((level, node["children"]))

    def render_nodes(nodes: list[dict[str, Any]], depth: int = 1) -> str:
        items = []
        for node in nodes:
            title_html = html.escape(node["title"])
            link_html = f'<a class="toc-link" href="#{node["hid"]}">{title_html}</a>'
            if node["children"]:
                open_attr = ''
                children_html = render_nodes(node["children"], depth + 1)
                body_html = f'<div class="toc-children">{children_html}</div>'
                items.append(
                    f'<li class="toc-item toc-depth-{depth}">'
                    f'<details class="toc-branch toc-depth-{depth}"{open_attr}>'
                    f'<summary>{link_html}</summary>'
                    f'{body_html}'
                    f'</details>'
                    f'</li>'
                )
            else:
                items.append(f'<li class="toc-item toc-depth-{depth}">{link_html}</li>')
        return f'<ul>{"".join(items)}</ul>'

    return f'<nav id="TableOfContents">{render_nodes(root)}</nav>'

def refresh_post_toc(post: PostRecord) -> PostRecord:
    # ??????????????????????
    if not post.body_html:
        return post
    soup = BeautifulSoup(post.body_html, "html.parser")
    headings = []
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        heading_id = tag.get("id", "").strip()
        title = tag.get_text(strip=True)
        if not heading_id or not title:
            continue
        headings.append((int(tag.name[1]), heading_id, title))
    post.toc_html = build_toc(headings)
    return post

def render_markdown(text: str) -> tuple[str, str, str, int]:
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    out, headings, plain = [], [], []
    used = set()
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            out.append(f'<div class="highlight"><pre tabindex="0"><code class="language-{html.escape(lang)}" data-lang="{html.escape(lang)}">{html.escape(chr(10).join(block))}</code></pre></div>')
            plain.append("\n".join(block))
            i += 1
            continue
        match = HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            hid = slugify_heading(title, used)
            out.append(f'<h{level} id="{hid}">{render_inline(title)}</h{level}>')
            headings.append((level, hid, title))
            plain.append(title)
            i += 1
            continue
        if line in {"---", "***", "___"}:
            out.append("<hr>")
            i += 1
            continue
        if line.startswith(">"):
            parts = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                parts.append(lines[i].strip()[1:].lstrip())
                i += 1
            quote_html, _, quote_text, _ = render_markdown("\n".join(parts))
            out.append(f"<blockquote>{quote_html}</blockquote>")
            plain.append(quote_text)
            continue
        if ORDERED_RE.match(line) or UNORDERED_RE.match(line):
            tag = "ol" if ORDERED_RE.match(line) else "ul"
            items = []
            while i < len(lines):
                current = lines[i].strip()
                matched = ORDERED_RE.match(current) if tag == "ol" else UNORDERED_RE.match(current)
                if not matched:
                    break
                items.append(f"<li>{render_inline(matched.group(1).strip())}</li>")
                plain.append(matched.group(1).strip())
                i += 1
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue
        paragraph = [line]
        i += 1
        while i < len(lines):
            current = lines[i].strip()
            if not current or current.startswith(("```", ">", "#")) or ORDERED_RE.match(current) or UNORDERED_RE.match(current) or current in {"---", "***", "___"}:
                break
            paragraph.append(current)
            i += 1
        text_block = " ".join(paragraph)
        out.append(f"<p>{render_inline(text_block)}</p>")
        plain.append(text_block)
    body = "\n".join(out)
    plain_text = "\n".join(item for item in plain if item).strip()
    words = len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", plain_text))
    return body, build_toc(headings), plain_text, words

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(content)

def page(title: str, path: str, content: str, desc: str = "", og_type: str = "website", published: str = "") -> str:
    return BASE.render(title=title, desc=f"{SITE_DESCRIPTION}{desc}" if desc else SITE_DESCRIPTION, canonical=abs_url(path), og_desc=desc, og_type=og_type, content=content, year=dt.datetime.now().year, site_url=SITE_URL, site_title=SITE_TITLE, published=published)

def state_path(site_root: Path) -> Path:
    return site_root / "scripts" / STATE_FILE

def save_state(site_root: Path, posts: list[PostRecord], sections: dict[str, SectionInfo]) -> None:
    posts = [post for post in posts if is_publishable_post(post)]
    data = {"posts": [asdict(post) for post in posts], "sections": {slug: asdict(info) for slug, info in sections.items()}}
    write_text(state_path(site_root), json.dumps(data, ensure_ascii=False, indent=2))

def parse_taxonomy_membership(root: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    if not root.exists():
        return mapping
    for file in root.rglob("index.html"):
        rel = file.relative_to(root).as_posix()
        if rel == "index.html" or "/page/" in rel:
            continue
        name = Path(rel).parts[0]
        soup = BeautifulSoup(file.read_text(encoding="utf-8"), "html.parser")
        for anchor in soup.select(".blog-card h3 a"):
            href = anchor.get("href", "").strip("/")
            if href.startswith("list/"):
                mapping[href].add(name)
    return mapping

def bootstrap(site_root: Path) -> tuple[list[PostRecord], dict[str, SectionInfo]]:
    posts, sections = [], {"list": SectionInfo(slug="list", title="目录", parent="", order=0)}
    order = 1
    for file in (site_root / "list").rglob("index.html"):
        soup = BeautifulSoup(file.read_text(encoding="utf-8"), "html.parser")
        article = soup.select_one("article.blog-single")
        rel = file.relative_to(site_root).as_posix()
        if article:
            parts = rel.split("/")
            body = article.select_one(".blog-content")
            toc = article.select_one(".blog-toc nav")
            meta_desc = soup.find("meta", attrs={"name": "description"})
            published = soup.find("meta", attrs={"property": "article:published_time"})
            title = article.select_one("header.blog-title h1").get_text(strip=True)
            text = body.get_text("\n", strip=True) if body else ""
            words = len(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text))
            posts.append(PostRecord(slug=parts[-2], title=title, source_note="", summary=(meta_desc.get("content", "").replace(SITE_DESCRIPTION, "", 1).strip() if meta_desc else ""), date_iso=published.get("content", dt.datetime.now().isoformat()) if published else dt.datetime.now().isoformat(), word_count=words, reading_minutes=max(1, math.ceil(words / 200)), rel_permalink="/".join(parts[:-1]), section_path=parts[1:-2], body_html="".join(str(x) for x in body.contents) if body else "", toc_html=str(toc) if toc else "", article_body_text=text))
            for depth in range(len(parts[1:-2])):
                slug = "/".join(["list", *parts[1: depth + 2]])
                if slug not in sections:
                    sections[slug] = SectionInfo(slug=slug, title=parts[depth + 1], parent="/".join(["list", *parts[1: depth + 1]]) if depth else "list", order=order)
                    order += 1
    for file in (site_root / "list").rglob("index.html"):
        soup = BeautifulSoup(file.read_text(encoding="utf-8"), "html.parser")
        if soup.select_one("article.blog-single"):
            continue
        rel = file.relative_to(site_root).as_posix()
        slug = rel[:-10] if rel.endswith("/index.html") else rel
        sections.setdefault(slug, SectionInfo(slug=slug, title=soup.title.get_text(strip=True) if soup.title else Path(slug).name, parent="/".join(slug.split("/")[:-1]), order=order))
        for anchor in soup.select(".blog-card h3 a"):
            href = anchor.get("href", "").strip("/")
            if href in sections:
                sections[href].title = anchor.get_text(strip=True)
    featured = set()
    if (site_root / "index.html").exists():
        soup = BeautifulSoup((site_root / "index.html").read_text(encoding="utf-8"), "html.parser")
        featured = {anchor.get("href", "").strip("/") for anchor in soup.select(".featured-single h4 a")}
    category_map = parse_taxonomy_membership(site_root / "categories")
    tag_map = parse_taxonomy_membership(site_root / "tags")
    for post in posts:
        post.featured = post.rel_permalink.strip("/") in featured
        post.categories = sorted(category_map.get(post.rel_permalink.strip("/"), []))
        post.tags = sorted(tag_map.get(post.rel_permalink.strip("/"), []))
    posts = [post for post in posts if is_publishable_post(post)]
    posts.sort(key=lambda item: item.date_iso, reverse=True)
    return posts, sections

def load_state(site_root: Path) -> tuple[list[PostRecord], dict[str, SectionInfo]]:
    file = state_path(site_root)
    if file.exists():
        data = json.loads(file.read_text(encoding="utf-8"))
        posts = [refresh_post_toc(PostRecord(**item)) for item in data.get("posts", [])]
        posts = [post for post in posts if is_publishable_post(post)]
        return posts, {slug: SectionInfo(**info) for slug, info in data.get("sections", {}).items()}
    return bootstrap(site_root)

def summary_from_text(text: str) -> str:
    return " ".join(text.split())[:180].strip()

def minute_text(post: PostRecord) -> str:
    date = parse_date(post.date_iso)
    return f"{calendar.month_name[date.month]} {date.day}, {date.year}&nbsp;· {post.word_count} words&nbsp;· {post.reading_minutes} min"

def render_post_card(post: PostRecord) -> str:
    return f'<article><div class="blog-card"><h3><a href="/{quote_path(post.rel_permalink).strip("/")}">{html.escape(post.title)}</a></h3><p><small>{minute_text(post)}</small><p><p>{html.escape(post.summary)}</p></div></article>'

def render_section_card(section: SectionInfo) -> str:
    return f'<article><div class="blog-card"><h3><a href="/{quote_path(section.slug).strip("/")}">{html.escape(section.title)}</a></h3></div></article>'

def render_listing(title: str, canonical_path: str, posts: list[PostRecord], children: list[SectionInfo], desc: str = "") -> str:
    content = f'<div class="blog-wrapper"><div><div class="blog-list">{"".join(render_post_card(post) for post in posts)}</div><div class="blog-list">{"".join(render_section_card(section) for section in children)}</div></div></div>'
    return page(title, canonical_path, content, desc)

def render_home(posts: list[PostRecord]) -> str:
    cards = []
    # ?????????????????????????????
    for post in posts[:HOME_POST_LIMIT]:
        cards.append(
            f'<article class="featured-single"><h4><a href="/{quote_path(post.rel_permalink).strip("/")}">{html.escape(post.title)}</a></h4><p><small>{minute_text(post)}</small><p></article>'
        )

    content = (
        '<div class="home">'
        '<section class="intro" style="display:flex;align-items:flex-start;justify-content:space-between;gap:2rem;margin:0 0 2.5rem;flex-wrap:wrap;">'
        '<div class="intro-content" style="flex:1;min-width:260px;">'
        f'<h1>{html.escape(INTRO_TITLE)}</h1>'
        f'<p class="intro-subtitle">{html.escape(INTRO_SUBTITLE)}</p>'
        f'<p class="intro-text">{html.escape(INTRO_TEXT)}</p>'
        '</div>'
        f'<div class="intro-avatar" style="flex:0 0 auto;"><img src="{html.escape(AVATAR)}" alt="{html.escape(INTRO_TITLE)}" style="width:120px;height:120px;border-radius:9999px;object-fit:cover;display:block;"></div>'
        '</section>'
        '<div class="featured">'
        '<h2>Latest Posts</h2>'
        f'<div class="featured-list">{"".join(cards)}</div>'
        '</div>'
        '</div>'
    )
    return page(SITE_TITLE, "", content)

def render_archive(posts: list[PostRecord]) -> str:
    grouped: dict[int, dict[int, list[PostRecord]]] = defaultdict(lambda: defaultdict(list))
    for post in posts:
        date = parse_date(post.date_iso)
        grouped[date.year][date.month].append(post)
    years = []
    for year in sorted(grouped.keys(), reverse=True):
        months = []
        for month in sorted(grouped[year].keys(), reverse=True):
            entries = []
            for post in grouped[year][month]:
                entries.append(f'<div class="archive-entry"><h3 class="archive-entry-title">{html.escape(post.title)}</h3><div class="archive-meta"><p><small>{minute_text(post)}</small><p></div><a class="archive-link" href="{abs_url(post.rel_permalink)}"></a></div>')
            months.append(f'<div class="archive-month"><h3 class="archive-month-header">{calendar.month_name[month]}<sup class="archive-count">&nbsp;&nbsp;{len(grouped[year][month])}</sup></h3><div class="archive-posts">{"".join(entries)}</div></div>')
        years.append(f'<div class="archive-year"><h2 class="archive-year-header">{year}<sup class="archive-count">&nbsp;&nbsp;{sum(len(v) for v in grouped[year].values())}</sup></h2>{"".join(months)}</div>')
    return page("归档", "archives", f'<div class="archive"><div class="archive-content">{"".join(years)}</div></div>', "归档 - Hzhsec home")

def render_taxonomy_root(title: str, base: str, bucket: dict[str, list[PostRecord]]) -> str:
    items = [f'<li><a href="{abs_url(f"{base}/{taxonomy_slug(name)}")}">{html.escape(name)}<small>({len(posts)})</small></a></li>' for name, posts in bucket.items()]
    return page(title, base, f'<div class="tags"><ul class="tags-list">{"".join(items)}</ul></div>')

def render_article(post: PostRecord, prev_post: Optional[PostRecord], next_post: Optional[PostRecord]) -> str:
    paginator = []
    if prev_post or next_post:
        paginator.append('<div class="paginator">')
        if prev_post:
            paginator.append(
                f'<a class="prev" href="{abs_url(prev_post.rel_permalink)}"><small>← 上一篇</small><span>{html.escape(prev_post.title)}</span></a>'
            )
        if next_post:
            paginator.append(
                f'<a class="next" href="{abs_url(next_post.rel_permalink)}"><small>下一篇 →</small><span>{html.escape(next_post.title)}</span></a>'
            )
        paginator.append('</div>')
    toc_block = f'<details class="blog-toc" open><summary>Contents</summary>{post.toc_html}</details>' if post.toc_html else ''
    content = f'<article class="blog-single"><header class="blog-title"><h1>{html.escape(post.title)}</h1></header><p><small>{minute_text(post)}</small><p>{toc_block}<section class="blog-content">{post.body_html}</section>{"".join(paginator)}</article>'
    return page(post.title, post.rel_permalink, content, post.summary, "article", post.date_iso)

def build_note(note_path: Path, existing: Optional[PostRecord], sections: dict[str, SectionInfo]) -> PostRecord:
    note_file = note_path.resolve()
    meta, body = parse_front_matter(note_path.read_text(encoding="utf-8"))
    body = body.lstrip("\ufeff").lstrip()
    if body.startswith("---"):
        body = body[3:].lstrip()
    title = normalize_text(meta.get("title")) or note_path.stem
    raw_section = (
        meta.get("section")
        or meta.get("path")
        or meta.get("dir")
        or meta.get("sections")
        or meta.get("_fallback_section")
    )
    section_path = normalize_list(raw_section)
    if len(section_path) == 1 and "/" in section_path[0]:
        section_path = [item for item in section_path[0].split("/") if item]
    if not section_path:
        guessed = sanitize_segment(note_file.parent.name)
        section_path = [guessed] if guessed else []
    if not section_path:
        raise ValueError("???????? section??? ????/linux")
    section_path = [sanitize_segment(item) for item in section_path]
    titles = meta.get("section_titles") or {}
    for depth in range(len(section_path)):
        slug = "/".join(["list", *section_path[: depth + 1]])
        parent = "/".join(["list", *section_path[: depth]]) if depth else "list"
        if slug not in sections:
            name = titles.get(section_path[depth]) or titles.get("/".join(section_path[: depth + 1])) or section_path[depth]
            sections[slug] = SectionInfo(slug=slug, title=name, parent=parent, order=len(sections) + 1)
    slug = sanitize_segment(normalize_text(meta.get("slug")) or note_path.stem)
    body_html, toc_html, plain, words = render_markdown(body)
    note_date = parse_date(meta.get("date") or dt.datetime.fromtimestamp(note_file.stat().st_mtime, tz=dt.timezone(dt.timedelta(hours=8))))
    post = PostRecord(slug=slug, title=title, source_note=str(note_path), summary=normalize_text(meta.get("summary")) or summary_from_text(plain), date_iso=note_date.isoformat(), word_count=words, reading_minutes=max(1, math.ceil(words / 200)), rel_permalink="/".join(["list", *section_path, slug]), section_path=section_path, categories=normalize_list(meta.get("categories")), tags=normalize_list(meta.get("tags")), featured=bool(meta.get("featured", False)) or (existing.featured if existing else False), body_html=body_html, toc_html=toc_html, article_body_text=plain)
    return post

def upsert(posts: list[PostRecord], post: PostRecord) -> list[PostRecord]:
    result = [item for item in posts if item.rel_permalink != post.rel_permalink]
    result.append(post)
    result = [item for item in result if is_publishable_post(item)]
    result.sort(key=lambda item: item.date_iso, reverse=True)
    return result

def detect_publish_action(posts: list[PostRecord], post: PostRecord, source_note: str = "") -> str:
    """??????????????"""
    if any(item.rel_permalink == post.rel_permalink for item in posts):
        return "NEW"
    if source_note and any(item.source_note == source_note for item in posts):
        return "NEW"
    return "NEW"

def rebuild(site_root: Path, posts: list[PostRecord], sections: dict[str, SectionInfo]) -> None:
    posts = [item for item in posts if is_publishable_post(item)]
    posts.sort(key=lambda item: item.date_iso, reverse=True)
    write_text(site_root / "index.html", render_home(posts))
    write_text(site_root / "archives" / "index.html", render_archive(posts))
    categories: dict[str, list[PostRecord]] = defaultdict(list)
    tags: dict[str, list[PostRecord]] = defaultdict(list)
    for post in posts:
        for item in post.categories:
            categories[item].append(post)
        for item in post.tags:
            tags[item].append(post)
    write_text(site_root / "categories" / "index.html", render_taxonomy_root("Categories", "categories", dict(sorted(categories.items()))))
    write_text(site_root / "tags" / "index.html", render_taxonomy_root("Tags", "tags", dict(sorted(tags.items()))))
    for name, grouped in categories.items():
        slug = taxonomy_slug(name)
        html_page = render_listing(name, f"categories/{slug}", grouped, [])
        write_text(site_root / "categories" / slug / "index.html", html_page)
        write_text(site_root / "categories" / slug / "page" / "1" / "index.html", html_page)
    for name, grouped in tags.items():
        slug = taxonomy_slug(name)
        html_page = render_listing(name, f"tags/{slug}", grouped, [])
        write_text(site_root / "tags" / slug / "index.html", html_page)
        write_text(site_root / "tags" / slug / "page" / "1" / "index.html", html_page)
    section_posts: dict[str, list[PostRecord]] = defaultdict(list)
    section_children: dict[str, list[SectionInfo]] = defaultdict(list)
    present = {"list"}
    for post in posts:
        section_slug = "/".join(["list", *post.section_path])
        section_posts[section_slug].append(post)
        for depth in range(len(post.section_path)):
            present.add("/".join(["list", *post.section_path[: depth + 1]]))
    for slug, info in sections.items():
        if slug != "list" and slug not in present:
            continue
        if slug != "list":
            section_children[info.parent].append(info)
    for group in section_children.values():
        group.sort(key=lambda item: (item.order, item.title.lower()))
    for slug, info in sections.items():
        if slug != "list" and slug not in present:
            continue
        html_page = render_listing(info.title, slug, sorted(section_posts.get(slug, []), key=lambda item: item.date_iso, reverse=True), section_children.get(slug, []), "This is the first chapter." if slug == "list" else "")
        target = site_root / Path(*slug.split('/')) / "index.html"
        write_text(target, html_page)
        if slug != "list":
            write_text(site_root / Path(*slug.split('/')) / "page" / "1" / "index.html", html_page)
    for index, post in enumerate(posts):
        prev_post = posts[index + 1] if index + 1 < len(posts) else None
        next_post = posts[index - 1] if index > 0 else None
        write_text(site_root / Path(*post.rel_permalink.split('/')) / "index.html", render_article(post, prev_post, next_post))

def backup(site_root: Path, note_path: Path, slug: str) -> None:
    target = site_root / "static" / "obsidian-notes"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(note_path, target / f"{slug}.md")


def collect_note_paths(note_input: str, batch: bool) -> list[Path]:
    """?????? Markdown ?????"""
    note_path = Path(note_input).expanduser().resolve()
    if not note_path.exists():
        raise FileNotFoundError(f"File or directory not found: {note_path}")
    if batch:
        if not note_path.is_dir():
            raise ValueError("--batch can only be used with a directory")
        return sorted(
            path
            for path in note_path.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".markdown"}
        )
    if note_path.is_dir():
        raise ValueError("Use --batch when passing a directory")
    return [note_path]


def publish_notes(
    site_root: Path,
    posts: list[PostRecord],
    sections: dict[str, SectionInfo],
    note_paths: list[Path],
    dry_run: bool,
    no_backup: bool,
) -> tuple[list[PostRecord], list[str], list[PostRecord]]:
    """??????????????????????"""
    results: list[str] = []
    published_posts: list[PostRecord] = []
    current_posts = posts
    for note_path in note_paths:
        existing = next((item for item in current_posts if item.source_note == str(note_path)), None)
        post = build_note(note_path, existing, sections)
        action_text = detect_publish_action(current_posts, post, str(note_path))
        current_posts = upsert(current_posts, post)
        results.append(f"{action_text}?{post.title} -> /{post.rel_permalink}/")
        published_posts.append(post)
        if not dry_run and not no_backup:
            backup(site_root, note_path, post.slug)
    return current_posts, results, published_posts


def run_git(site_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """?? git ????????"""
    return subprocess.run(
        ["git", *args],
        cwd=str(site_root),
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def auto_git_push(site_root: Path, message: str) -> str:
    """????????????"""
    status = run_git(site_root, ["status", "--short"]).stdout.strip()
    if not status:
        return "No git changes detected, skipped commit and push"

    run_git(site_root, ["add", "-A"])
    run_git(site_root, ["commit", "-m", message])
    push_result = run_git(site_root, ["push"])
    output = (push_result.stdout or push_result.stderr).strip()
    return f"Git push done: {message}" + (f"\n{output}" if output else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Markdown from Obsidian to site")
    parser.add_argument("note", nargs="?", help="Obsidian note file or directory")
    parser.add_argument("--site-root", default=str(DEFAULT_SITE_ROOT))
    parser.add_argument("--batch", action="store_true", help="Publish all Markdown files in a directory")
    parser.add_argument("--rebuild-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--git-push", action="store_true", help="Run git add/commit/push after publishing")
    parser.add_argument("--commit-message", default="", help="Custom git commit message")
    configure_windows_console()
    args = parser.parse_args()
    site_root = Path(args.site_root).expanduser().resolve()
    posts, sections = load_state(site_root)
    if args.rebuild_only:
        if args.dry_run:
            print(f"PREVIEW READY: {state_path(site_root)}")
            return 0
        rebuild(site_root, posts, sections)
        save_state(site_root, posts, sections)
        print(f"REBUILD DONE: {len(posts)} posts")
        if args.git_push:
            message = args.commit_message.strip() or f"rebuild site {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            print(auto_git_push(site_root, message))
        return 0
    if not args.note:
        parser.error("Please provide a note path or use --rebuild-only")
    note_paths = collect_note_paths(args.note, args.batch)
    if args.batch and not note_paths:
        raise ValueError("No Markdown files found in the directory")
    posts, results, published_posts = publish_notes(
        site_root,
        posts,
        sections,
        note_paths,
        args.dry_run,
        args.no_backup,
    )
    if args.dry_run:
        for line in results:
            print(line.replace("?", " PREVIEW: ", 1))
        if published_posts:
            print(f"TOTAL: {len(published_posts)}")
        return 0
    rebuild(site_root, posts, sections)
    save_state(site_root, posts, sections)
    for line in results:
        print(line.replace("?", " DONE: ", 1))
    if args.batch:
        print(f"BATCH DONE: {len(published_posts)}")
    if args.git_push:
        default_message = f"batch publish {len(published_posts)} posts" if args.batch else f"publish {published_posts[-1].title}"
        message = args.commit_message.strip() or default_message
        print(auto_git_push(site_root, message))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
