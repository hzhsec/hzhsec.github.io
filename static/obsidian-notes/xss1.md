---
title: "XSS1"
slug: xss1
cover: ""
date: 2024-04-08
categories:
  - 杂项
halo:
  site: http://www.hzhsec.top
  name: 5060a958-3980-4f4e-9eeb-53d0fe2c1260
  publish: true
---

<!--more-->

# XSS 跨站 — 输入/输出、原理、分类与闭合

**漏洞概述**  
XSS（跨站脚本）本质上是：**接收外部输入 → 输出到页面并被浏览器解析/执行**。根据输入/输出的保存与执行位置，XSS 可以分为反射型、存储型、DOM 型等。

---

## 漏洞原理
**原理简述**：应用接收不可信输入并在输出时未做适当处理（或客户端脚本不安全地使用这些数据），导致攻击者构造的脚本在受害者浏览器中执行。  
关键链路：**输入点 → 服务器/客户端处理 → 输出到页面上下文 → 浏览器执行**。

---

## 基础类型

### 反射型（Reflected XSS）
**定义**：攻击载荷随请求参数发送，服务器在响应中直接回显（不持久化）。通常通过构造恶意链接诱导用户点击从而触发一次性攻击（one-to-one）。  
**常见场景**：
- 搜索、错误消息、重定向参数直接回显
- 表单回填未编码
**检测要点**：向参数注入探针，观察响应是否按预期回显并执行。

**示意：反射型 XSS 攻击流程图**  
<img src="/static/image 1.jpg" alt="反射型 XSS 流程图">

---

### 存储型（Stored XSS）
**定义**：恶意脚本被服务器持久化（如数据库、留言、评论、用户资料等），当其他用户查看包含该内容的页面时触发执行（one-to-many），危害范围更广。  
**常见场景**：
- 评论、论坛发帖、富文本编辑器内容存储后回显  
- 用户资料（昵称、签名）被当作 HTML 回显  
**检测要点**：在能写入后端存储的位置注入 payload，随后访问回显页面查看是否执行。

**示意：存储型 XSS 攻击流程图**  
<img src="/static/image1.jpg" alt="存储型 XSS 流程图">

---

### DOM 型（DOM-based XSS）
**定义**：漏洞发生在浏览器端。页面的 JavaScript 将来自 `location`、`hash`、`document.referrer`、`postMessage`、`localStorage` 等来源的数据不安全地写入 DOM（例如使用 `innerHTML`、`document.write`、`eval`），从而触发脚本执行。服务器响应本身可能“干净”。  
**特点**：
- 发生/触发都在客户端（浏览器）侧  
- 需要审计前端 JS 的数据流（source → sink）  
**检测要点**：在浏览器环境修改 `location.hash`/`location.search` 或模拟 postMessage，然后观察 DOM 是否被不安全插入或执行。

**示意：HTML DOM 树形结构（便于理解数据如何被插入 DOM）**  
<img src="/static/image2 2.jpg" alt="HTML DOM 树形结构">

---

## 拓展类型与常见载体
- jQuery 相关不当 API 使用导致的 XSS（如 `.html()` 直接插入未经消毒的内容）  
- MXSS / UXSS / PDF XSS / Flash XSS / 上传类 XSS（文件名、图片 EXIF、SVG 等）  
- 富文本编辑器（富文本内容若未严格过滤或未使用安全 sanitizer，极易引入 Stored XSS）

---

## 攻击利用与可能后果
常见利用方式与影响包括但不限于：
- 恶意重定向、页面劫持  
- cookie / 会话凭证窃取（若 cookie 非 HttpOnly）  
- 持久化的钓鱼页面或权限维持（植入后门）  
- 行为伪造（利用受害者权限在后台操作）

---

## 测试流程与检测点（实用步骤）
1. **发现输入点**：所有能提交/控制内容的字段（GET、POST、Headers、文件上传、富文本）。  
2. **观察输出点**：页面回显、模板渲染、JS DOM 操作、动态模板/脚本注入位置。  
3. **注入探针**：从简单的 `"<script>alert(1)</script>` 到更隐蔽的 payload（可绕过过滤器）逐步测试。  
4. **针对 DOM XSS**：在浏览器 Console 手动或脚本化地修改 `location.search/hash`、`postMessage`、`localStorage`，观察是否被 JS 插入到危险 sink（`innerHTML`、`eval` 等）。  
5. **记录与证据**：截图/持久化日志/response 保存，便于复现与修复跟踪。  
6. **避免盲测生产**：若为生产环境，优先使用抽样与低频率测试并在授权范围内进行。

---

## 安全修复与防护要点
- **输出编码（上下文相关）**：HTML、Attribute、JavaScript、URL 等按上下文进行编码。  
- **尽量避免危险 API**：前端尽量不用 `innerHTML` / `document.write` / `eval`，而用 `textContent`、`createTextNode` 等。  
- **使用成熟的 Sanitizer**：如 DOMPurify 等，在必须允许部分 HTML 的场景中清洗输入。  
- **Content Security Policy（CSP）**：配置严格的 CSP（禁用 `unsafe-inline`、限制 script 源），降低攻击影响范围。  
- **HttpOnly / Secure / SameSite Cookie**：防止 JS 直接读取 cookie，并降低 CSRF 等风险。  
- **White-list 验证**：对输入采用白名单策略，尤其是对可插入 DOM 的参数进行严格校验。  
- **WAF 与检测**：部署 WAF 作第一道防线，但不要依赖 WAF 替代编码/消毒（WAF 可作为补充）。  
- **最小化数据暴露**：页面尽量不输出敏感信息（例如完整 cookie、token），只输出必要数据。

---

## 常见测试点汇总
- 用户资料、签名、昵称回显点  
- 评论/论坛/富文本编辑器内容  
- 文件名、图片元数据（EXIF、SVG）  
- URL 参数（query、fragment/hash）、referer、postMessage、localStorage 内容  
- 第三方组件（WYSIWYG 编辑器、插件）未正确配置或未消毒内容的地方

---

## 小结
- **反射型**：一次性回显，常通过恶意链接触发。  
- **存储型**：持久化到服务器，影响范围广，危害大。  
- **DOM 型**：客户端脚本不安全处理数据导致执行，服务器端响应可能并未直接包含 payload。  

---