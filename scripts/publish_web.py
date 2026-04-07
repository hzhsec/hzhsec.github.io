#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""本地网页表单发布 Obsidian 笔记。"""

from __future__ import annotations

import argparse
import html
import json
import sys
import yaml
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publish_obsidian as pub

HOST = "0.0.0.0"
PORT = 8765

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Obsidian 发布器</title>
  <style>
    :root {
      --bg: #f5efe6;
      --panel: #fffdf9;
      --line: #d8c9b6;
      --text: #2f241d;
      --muted: #7c6757;
      --brand: #b65d3a;
      --brand-dark: #8f4324;
      --ok: #2f7d4a;
      --warn: #a25a17;
      --shadow: 0 18px 40px rgba(86, 58, 39, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "LXGW WenKai", "Microsoft YaHei", sans-serif;
      background: radial-gradient(circle at top left, #fff8ef 0%, var(--bg) 55%, #efe3d3 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 20px 60px;
    }
    .hero {
      margin-bottom: 22px;
    }
    .hero h1 {
      margin: 0 0 8px;
      font-size: 34px;
    }
    .hero p {
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
      padding: 22px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .full { grid-column: 1 / -1; }
    label {
      display: block;
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 12px;
      padding: 12px 14px;
      font: inherit;
      outline: none;
    }
    input:focus, textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(182, 93, 58, 0.12);
    }
    textarea {
      min-height: 100px;
      resize: vertical;
    }
    .hint {
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }
    .actions {
      display: flex;
      gap: 12px;
      align-items: center;
      margin-top: 20px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 20px;
      font: inherit;
      cursor: pointer;
      transition: .18s ease;
    }
    .primary {
      background: var(--brand);
      color: #fff;
    }
    .primary:hover { background: var(--brand-dark); }
    .ghost {
      background: #efe2d5;
      color: var(--text);
    }
    .ghost:hover { background: #e5d3c3; }
    .notice {
      margin-top: 18px;
      border-radius: 14px;
      padding: 14px 16px;
      white-space: pre-wrap;
      line-height: 1.6;
      border: 1px solid var(--line);
    }
    .notice.ok {
      background: #edf8f1;
      border-color: #b8ddc5;
      color: var(--ok);
    }
    .notice.err {
      background: #fff1ea;
      border-color: #ebc0aa;
      color: #9f4123;
    }
    .notice.info {
      background: #fff8e9;
      border-color: #ecd6a0;
      color: var(--warn);
    }
    .row-inline {
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .checkbox {
      width: auto;
      margin-right: 8px;
    }
    code {
      background: #f1e6d8;
      padding: 2px 6px;
      border-radius: 6px;
    }
    @media (max-width: 760px) {
      .grid { grid-template-columns: 1fr; }
      .wrap { padding: 20px 14px 40px; }
      .hero h1 { font-size: 28px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>Obsidian 本地发布器</h1>
      <p>不改原始 Markdown，直接填空后发布到当前静态站点。</p>
    </div>

    <form class="card" method="post" enctype="multipart/form-data">
      <div class="grid">
        <div class="full">
          <label for="note_file">选择 Markdown 笔记</label>
          <input id="note_file" name="note_file" type="file" accept=".md,.markdown,text/markdown">
          <div class="hint">直接从 Obsidian 里把 md 文件拖进来即可，脚本不会修改你的原文件。</div>
        </div>

        <div>
          <label for="title">标题</label>
          <input id="title" name="title" type="text" placeholder="文章标题">
        </div>

        <div>
          <label for="date">发布日期</label>
          <input id="date" name="date" type="text" placeholder="2026-04-07 21:30">
        </div>

        <div>
          <label for="section">目录路径</label>
          <input id="section" name="section" type="text" placeholder="权限提升/linux">
          <div class="hint">会发布到 <code>/list/权限提升/linux/文章slug/</code></div>
        </div>

        <div>
          <label for="slug">Slug</label>
          <input id="slug" name="slug" type="text" placeholder="留空则默认取文件名">
        </div>

        <div>
          <label for="categories">分类</label>
          <input id="categories" name="categories" type="text" placeholder="Linux提权, Web安全">
        </div>

        <div>
          <label for="tags">标签</label>
          <input id="tags" name="tags" type="text" placeholder="提权, Obsidian, 测试">
        </div>

        <div class="full">
          <label for="summary">摘要</label>
          <textarea id="summary" name="summary" placeholder="留空则默认取正文前一段"></textarea>
        </div>

        <div class="full">
          <label for="section_titles">栏目显示名映射</label>
          <input id="section_titles" name="section_titles" type="text" placeholder='例如：linux=Linux; 权限提升=权限提升'>
          <div class="hint">只有新建目录时才需要。格式：<code>键=值; 键=值</code></div>
        </div>

        <div class="full row-inline">
          <label style="margin: 0;"><input class="checkbox" name="featured" type="checkbox">首页推荐</label>
          <label style="margin: 0;"><input class="checkbox" name="dry_run" type="checkbox" checked>仅预览，不写入文件</label>
          <label style="margin: 0;"><input class="checkbox" name="no_backup" type="checkbox">不备份源 md</label>
        </div>
      </div>

      <div class="actions">
        <button class="primary" type="submit">发布 / 预览</button>
        <button class="ghost" type="button" onclick="window.location.reload()">清空表单</button>
      </div>

      {message_block}
    </form>
  </div>
  <script>
    const form = document.querySelector("form.card");
    const fileInput = document.getElementById("note_file");
    const fields = {
      title: document.getElementById("title"),
      date: document.getElementById("date"),
      section: document.getElementById("section"),
      slug: document.getElementById("slug"),
      categories: document.getElementById("categories"),
      tags: document.getElementById("tags"),
      summary: document.getElementById("summary"),
      section_titles: document.getElementById("section_titles")
    };

    const notice = document.createElement("div");
    notice.className = "notice info";
    notice.style.display = "none";
    form.appendChild(notice);

    function showNotice(message, level = "info") {
      notice.className = `notice ${level}`;
      notice.textContent = message;
      notice.style.display = "block";
    }

    function fillIfEmpty(input, value) {
      if (!input || input.value.trim() || !value) return;
      input.value = value;
    }

    function applyMeta(meta) {
      fillIfEmpty(fields.title, meta.title || "");
      fillIfEmpty(fields.date, meta.date || "");
      fillIfEmpty(fields.section, meta.section || "");
      fillIfEmpty(fields.slug, meta.slug || "");
      fillIfEmpty(fields.categories, meta.categories || "");
      fillIfEmpty(fields.tags, meta.tags || "");
      fillIfEmpty(fields.summary, meta.summary || "");
      fillIfEmpty(fields.section_titles, meta.section_titles || "");
      return {
        title: fields.title.value,
        date: fields.date.value,
        section: fields.section.value,
        slug: fields.slug.value,
        categories: fields.categories.value,
        tags: fields.tags.value,
        summary: fields.summary.value,
        section_titles: fields.section_titles.value
      };
    }

    async function parseSelectedFile(file) {
      const data = new FormData();
      data.append("note_file", file, file.name);
      const response = await fetch("/parse", { method: "POST", body: data });
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        const rawText = await response.text();
        throw new Error(`?????? JSON ?????????????????????${rawText.slice(0, 80)}`);
      }
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "????");
      }
      const serverMeta = payload.meta || {};
      const filledMeta = applyMeta(serverMeta);
      showNotice(`??????${file.name}\n\n????????${JSON.stringify(serverMeta, null, 2)}\n\n??????${JSON.stringify(filledMeta, null, 2)}`, "ok");
    }

    fileInput.addEventListener("change", async (event) => {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      try {
        await parseSelectedFile(file);
      } catch (error) {
        showNotice(`?????${error.message || error}`, "err");
      }
    });
  </script>
</body>
</html>"""


def split_csv(value: str) -> list[str]:
    """将逗号分隔文本转为列表。"""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_section_titles(value: str) -> dict[str, str]:
    """解析 section_titles 的简写输入。"""
    result: dict[str, str] = {}
    for item in value.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, mapped = item.split("=", 1)
        key = key.strip()
        mapped = mapped.strip()
        if key and mapped:
            result[key] = mapped
    return result


def metadata_to_form_values(filename: str, content: bytes) -> dict[str, str]:
    """???? Markdown ??????????"""
    text = content.decode("utf-8-sig")
    meta, body = pub.parse_front_matter(text)
    body = body.lstrip("﻿").lstrip()
    if body.startswith("---"):
        body = body[3:].lstrip()

    title = pub.normalize_text(meta.get("title")) or Path(filename).stem
    heading_match = None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            heading_match = stripped[2:].strip()
            break
    if heading_match and not pub.normalize_text(meta.get("title")):
        title = heading_match

    raw_section = meta.get("section") or meta.get("path") or meta.get("dir") or meta.get("sections")
    section_value = ""
    if isinstance(raw_section, list):
        section_value = "/".join(str(item).strip() for item in raw_section if str(item).strip())
    elif raw_section is not None:
        section_value = str(raw_section).strip()

    section_titles = meta.get("section_titles") or {}
    if isinstance(section_titles, dict):
        section_titles_text = "; ".join(f"{key}={value}" for key, value in section_titles.items())
    else:
        section_titles_text = ""

    return {
        "title": title,
        "date": pub.normalize_text(meta.get("date")),
        "section": section_value,
        "slug": pub.normalize_text(meta.get("slug")) or Path(filename).stem,
        "categories": ", ".join(pub.normalize_list(meta.get("categories"))),
        "tags": ", ".join(pub.normalize_list(meta.get("tags"))),
        "summary": pub.normalize_text(meta.get("summary")),
        "section_titles": section_titles_text,
    }

def publish_uploaded_note(site_root: Path, filename: str, content: bytes, form: dict[str, Any]) -> str:
    """将上传的笔记内容发布到站点。"""
    posts, sections = pub.load_state(site_root)
    text = content.decode("utf-8-sig")

    # 用临时文件承接正文，但不会改动用户原始 md。
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_note = Path(tmp_dir) / filename
        with temp_note.open("w", encoding="utf-8", newline="") as file:
            file.write(text)

        metadata = {
            "title": form.get("title", "").strip(),
            "date": form.get("date", "").strip(),
            "section": form.get("section", "").strip(),
            "slug": form.get("slug", "").strip(),
            "categories": split_csv(form.get("categories", "")),
            "tags": split_csv(form.get("tags", "")),
            "summary": form.get("summary", "").strip(),
            "featured": form.get("featured") == "on",
            "section_titles": parse_section_titles(form.get("section_titles", "")),
            # ????????????????? section ???????????
            "_fallback_section": split_csv(form.get("categories", ""))[0] if not form.get("section", "").strip() and split_csv(form.get("categories", "")) else "",
        }

        meta, body = pub.parse_front_matter(text)
        meta.update({key: value for key, value in metadata.items() if value not in ("", [], {})})
        merged_text = "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n" + body if meta else body
        with temp_note.open("w", encoding="utf-8", newline="") as file:
            file.write(merged_text)

        existing = next((item for item in posts if item.source_note == str(temp_note)), None)
        post = pub.build_note(temp_note, existing, sections)
        post.source_note = filename
        posts = pub.upsert(posts, post)

        if form.get("dry_run") == "on":
            return f"预览成功\n\n标题：{post.title}\n路径：/{post.rel_permalink}/\n分类：{', '.join(post.categories) or '无'}\n标签：{', '.join(post.tags) or '无'}"

        pub.rebuild(site_root, posts, sections)
        pub.save_state(site_root, posts, sections)

        if form.get("no_backup") != "on":
            backup_dir = site_root / "static" / "obsidian-notes"
            backup_dir.mkdir(parents=True, exist_ok=True)
            with (backup_dir / filename).open("w", encoding="utf-8", newline="") as file:
                file.write(text)

        return f"发布完成\n\n标题：{post.title}\n路径：/{post.rel_permalink}/"


class PublishHandler(BaseHTTPRequestHandler):
    """?????????"""

    site_root: Path = Path.cwd()

    def do_GET(self) -> None:
        self.respond(message="", level="info")

    def parse_request_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError("??????????? multipart/form-data")
        import cgi
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(length),
        }
        temp = tempfile.SpooledTemporaryFile()
        temp.write(body)
        temp.seek(0)
        return cgi.FieldStorage(fp=temp, headers=self.headers, environ=environ)

    def do_POST(self) -> None:
        try:
            fs = self.parse_request_form()
            note_item = fs["note_file"] if "note_file" in fs else None
            if note_item is None or not getattr(note_item, "filename", ""):
                raise ValueError("?????? Markdown ??")

            route = self.path.rstrip("/") or "/"
            if route == "/parse":
                meta = metadata_to_form_values(Path(note_item.filename).name, note_item.file.read())
                self.respond_json({"ok": True, "meta": meta})
                return

            form = {
                key: fs.getvalue(key, "")
                for key in ["title", "date", "section", "slug", "categories", "tags", "summary", "section_titles", "featured", "dry_run", "no_backup"]
            }
            message = publish_uploaded_note(self.site_root, Path(note_item.filename).name, note_item.file.read(), form)
            level = "info" if form.get("dry_run") == "on" else "ok"
            self.respond(message=message, level=level)
        except Exception as error:
            route = self.path.rstrip("/") or "/"
            if route == "/parse":
                self.respond_json({"ok": False, "error": str(error)}, status=400)
                return
            self.respond(message=f"????\n\n{error}", level="err")

    def log_message(self, format: str, *args: object) -> None:
        return

    def respond(self, message: str, level: str) -> None:
        message_block = ""
        if message:
            message_block = f'<div class="notice {level}">{html.escape(message)}</div>'
        page = HTML_PAGE.replace("{message_block}", message_block)
        encoded = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def respond_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser(description="启动 Obsidian 本地网页发布器")
    parser.add_argument("--site-root", default=".", help="站点根目录，默认当前目录")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    PublishHandler.site_root = Path(args.site_root).resolve()
    server = ThreadingHTTPServer((args.host, args.port), PublishHandler)
    print(f"发布器已启动: http://{args.host}:{args.port}")
    print("浏览器打开这个地址，填表后即可发布。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
