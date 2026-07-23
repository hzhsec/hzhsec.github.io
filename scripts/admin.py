#!/usr/bin/env python3
"""🛠️ 博客管理后台 - 删文章 · 改分类 · 看列表"""
import json, os, shutil, sys, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

SITE_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = SITE_ROOT / "scripts" / "site_state.json"
PORT = 18001

CATEGORIES = ["Web安全","漏洞复现","权限提升","应急响应","XSS","SQL注入","SSRF","XXE","RCE","文件安全","工具使用","杂项","业务逻辑漏洞","云上攻防","内网渗透","环境搭建","护网","PHP安全","跨域安全","burpsuite靶场","top10","移动安全"]

def load_state():
    return json.loads(STATE_FILE.read_text("utf-8"))

def save_state(s):
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), "utf-8")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/":
            self.send_html(HTML)
        elif p == "/api/list":
            state = load_state()
            items = []
            for post in state.get("posts", []):
                cat = (post.get("categories") or ["杂项"])[0]
                items.append({"slug": post["slug"], "title": post.get("title",post["slug"]), "category": cat, "date": (post.get("date_iso") or "")[:10]})
            self.send_json(items)
        elif p.startswith("/api/get/"):
            slug = p.split("/api/get/")[-1]
            state = load_state()
            for post in state["posts"]:
                if post["slug"] == slug:
                    self.send_json(post)
                    return
            self.send_json({"error":"not found"})
        else:
            self.send_error(404)

    def do_POST(self):
        p = urlparse(self.path).path
        length = int(self.headers.get("Content-Length",0))
        data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        state = load_state()

        if p == "/api/delete":
            slug = data.get("slug","")
            before = len(state["posts"])
            state["posts"] = [po for po in state["posts"] if po["slug"] != slug]
            for d in SITE_ROOT.glob(f"list/*/{slug}"):
                shutil.rmtree(d, ignore_errors=True)
            save_state(state)
            self.send_json({"ok":True,"removed": before-len(state["posts"])})

        elif p == "/api/update":
            slug = data.get("slug","")
            for post in state["posts"]:
                if post["slug"] == slug:
                    if "title" in data: post["title"] = data["title"]
                    if "category" in data:
                        old_cat = (post.get("categories") or ["杂项"])[0]
                        post["categories"] = [data["category"]]
                        post["rel_permalink"] = f"list/{data['category']}/{slug}"
                        # 移动 HTML 目录
                        old_dir = SITE_ROOT / "list" / old_cat / slug
                        new_dir = SITE_ROOT / "list" / data["category"] / slug
                        if old_dir.exists() and old_cat != data["category"]:
                            new_dir.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(old_dir), str(new_dir))
                    if "tags" in data:
                        post["tags"] = [t.strip() for t in data["tags"].split(",") if t.strip()]
                    save_state(state)
                    self.send_json({"ok":True})
                    return
            self.send_json({"error":"not found"})
        else:
            self.send_json({"error":"unknown"})

    def send_json(self, d):
        self.send_response(200)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(d, ensure_ascii=False).encode("utf-8"))

    def send_html(self, h):
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(h.encode("utf-8"))

    def log_message(self, *a): pass


CATS_JSON = json.dumps(CATEGORIES, ensure_ascii=False)
HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🛠️ 博客管理</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f5f5f5;color:#333;padding:20px}
.hdr{background:#2d2d2d;color:#fff;padding:14px 20px;border-radius:8px;margin-bottom:16px;display:flex;justify-content:space-between}
.hdr h1{font-size:18px}
.row{display:flex;gap:16px}
.sd{width:240px;flex-shrink:0}
.mn{flex:1}
.srch{width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;margin-bottom:10px;font-size:13px}
.lst{background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.it{padding:10px 14px;border-bottom:1px solid #f0f0f0;cursor:pointer;display:flex;justify-content:space-between}
.it:hover{background:#f8f9ff}
.it .t{font-size:13px;font-weight:500}
.it .m{font-size:11px;color:#999;margin-top:2px}
.cat{display:inline-block;padding:1px 8px;border-radius:8px;background:#e8f0fe;color:#4a90d9;font-size:11px}
.sd .cat{padding:3px 10px;margin:2px;cursor:pointer;display:inline-block}
.sd .cat.act{background:#4a90d9;color:#fff}
.fm{background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:16px;display:none}
.fm h3{margin-bottom:12px;font-size:15px}
.fg{margin-bottom:10px}
.fg label{font-size:12px;color:#666;display:block;margin-bottom:2px}
.fg input,.fg select{width:100%;padding:7px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px}
.btn{padding:7px 16px;border:none;border-radius:6px;cursor:pointer;font-size:13px;margin-right:6px}
.b1{background:#4a90d9;color:#fff}
.b2{background:#e74c3c;color:#fff}
.b3{background:#fff;border:1px solid #ddd}
.st{background:#fff;border-radius:8px;padding:10px 14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.st .n{font-size:22px;font-weight:700}
.st .l{font-size:12px;color:#888}
.ct{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.empty{text-align:center;padding:30px;color:#999;font-size:13px}
</style></head>
<body>
<div class="hdr"><h1>🛠️ HZHsec 博客</h1><span><a href="/list/" style="color:#8cf" target="_blank">预览站点</a></span></div>
<div class="row">
<div class="sd">
<div class="st"><div class="n" id="tc">0</div><div class="l">文章</div></div>
<input class="srch" id="q" placeholder="搜索..." oninput="flt()">
<div class="ct" id="ct"></div>
</div>
<div class="mn">
<div class="fm" id="fm">
<h3 id="fmt">文章详情</h3>
<div class="fg"><label>标题</label><input id="et" oninput="d=1"></div>
<div class="fg"><label>Slug</label><input id="es" readonly style="background:#f5f5f5"></div>
<div class="fg"><label>分类</label><select id="ec" onchange="d=1"></select></div>
<div class="fg"><label>标签（逗号分隔）</label><input id="eg" oninput="d=1"></div>
<div><button class="btn b1" onclick="sv()">💾 保存</button><button class="btn b2" onclick="del()">🗑️ 删除</button><button class="btn b3" onclick="cls()">取消</button></div>
</div>
<div class="lst" id="lst"></div>
</div></div>
<script>
let all=[],cur='',d=0,cf='',sq='';

async function load(){const r=await fetch('/api/list');all=await r.json();
tc.textContent=all.length;
const m={};all.forEach(p=>{const c=p.category||'杂项';if(!m[c])m[c]=[];m[c].push(p)});
let h='<button onclick="sf(this,\'\')" class="cat act">全部</button>';
Object.keys(m).sort().forEach(c=>{h+=`<button onclick="sf(this,'${c}')" class="cat">${c} (${m[c].length})</button>`});
document.getElementById('ct').innerHTML=h;flt();}

function sf(el,c){cf=c;document.querySelectorAll('.ct .cat').forEach(b=>b.classList.remove('act'));el.classList.add('act');flt();}

function flt(){sq=document.getElementById('q').value.toLowerCase();
const f=all.filter(p=>{if(cf&&p.category!==cf)return false;if(sq&&!p.title.toLowerCase().includes(sq)&&!p.slug.toLowerCase().includes(sq))return false;return true});
const l=document.getElementById('lst');
if(!f.length){l.innerHTML='<div class="empty">无匹配</div>';return}
l.innerHTML=f.map(p=>`<div class="it" onclick="sd('${p.slug}')"><div><div class="t">${p.title}</div><div class="m"><span class="cat">${p.category}</span> ${p.date}</div></div></div>`).join('');}

async function sd(slug){cur=slug;d=0;
const r=await fetch('/api/get/'+slug);const p=await r.json();
if(p.error)return;
document.getElementById('fm').style.display='block';
document.getElementById('fmt').textContent='📄 '+p.title;
document.getElementById('et').value=p.title||'';
document.getElementById('es').value=p.slug||'';
const sel=document.getElementById('ec');sel.innerHTML='';
const cc=(p.categories||[])[0]||'杂项';
CATS.forEach(c=>{const o=document.createElement('option');o.value=c;o.text=c;if(c==cc)o.selected=true;sel.appendChild(o)});
document.getElementById('eg').value=(p.tags||[]).join(', ');}

async function sv(){if(!cur)return;
const r=await fetch('/api/update',{method:'POST',body:JSON.stringify({slug:cur,title:et.value,category:ec.value,tags:eg.value})});
const j=await r.json();
if(j.ok){alert('✅ 已保存');d=0;load();cls();}else alert('❌ 失败');}

async function del(){if(!cur||!confirm('删除「'+et.value+'」?'))return;
const r=await fetch('/api/delete',{method:'POST',body:JSON.stringify({slug:cur})});
const j=await r.json();
if(j.ok){alert('🗑️ 已删除');load();cls();}}

function cls(){document.getElementById('fm').style.display='none';d=0;}
const CATS=__CATS__;
load();
</script></body></html>'''.replace("__CATS__", CATS_JSON)

if __name__ == "__main__":
    os.chdir(str(SITE_ROOT))
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  🛠️  管理后台 http://localhost:{PORT}")
    print(f"  ⏹  Ctrl+C 停止")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 已停止")
        server.server_close()
