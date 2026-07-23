---
title: "Web 安全防御指南：CSP、HttpOnly 与 XSS Filter 深度解析"
slug: xss-defense-csp-httponly-filter
cover: ""
date: 2026-01-09
categories:
  - XSS
  - top10
tags:
  - XSS
  - 安全防御
  - 内容安全策略CSP
halo:
  site: http://www.hzhsec.top
  name: 09510276-dc23-4ef6-9e7a-bacf6e2a4323
  publish: true
---

<!--more-->
XSS 跨站 — 安全防御：CSP / HttpOnly / XSSFilter



下面整理了三类常见的 XSS 防御技术：CSP（Content Security Policy）、HttpOnly Cookie 与基于过滤/编码的 XSS 过滤器，包含原理、实践配置、实验提示与常见绕过/注意点。

---

## 一、CSP（Content Security Policy 内容安全策略）

内容安全策略是一种**可信白名单机制**，用于限制页面中可加载或执行的来源。浏览器根据网站返回的 CSP 头部决定允许哪些资源执行或加载，等于把执行/加载权限交给浏览器以白名单方式控制。

**主要作用**：

- 限制外域代码加载，降低复杂攻击逻辑的风险。  
- 限制敏感数据外传（限制 `connect-src` 等），防止被注入后外泄到任意域。  
- 禁止内联脚本执行（`'unsafe-inline'` 被禁用），可以阻断大量基于 inline script 的 XSS。  
- 结合 `report-uri` / `report-to` 能上报违反策略的事件，便于快速发现与修复。

**启用示例（PHP）**：

```php
header("Content-Security-Policy: default-src 'self'; img-src 'self' https://cdn.example.com; script-src 'self'; report-uri /csp-report-endpoint");
```

**优点**：浏览器端强制执行、能显著降低攻击面。  
**缺点/限制**：旧浏览器支持不完整；错误配置可能导致页面功能失效；某些绕过技巧（例如通过允许的第三方脚本链路）仍然可能被利用。

**参考与绕过研究**：

- 阿里云： https://xz.aliyun.com/t/12370  
- 绕过示例与研究： https://blog.csdn.net/a1766855068/article/details/89370320

---

## 二、HttpOnly（Cookie 标志）

**原理**：将敏感 cookie 标记为 `HttpOnly` 后，客户端 JavaScript 不再能通过 `document.cookie` 读取该 cookie，从而防止基于 XSS 的窃取（常用于会话 cookie）。

**配置示例**（PHP）：

```ini
; php.ini
session.cookie_httponly = 1
```

```php
// 在代码中设置
ini_set("session.cookie_httponly", 1);
setcookie('SESSIONID', $value, time()+3600, '/', '', false, true); // 最后一个 true 表示 HttpOnly
```

**注意与绕过**：

- HttpOnly 无法阻止攻击者通过 XSS 发起操作（例如用 XSS 发起受害者的授信操作），但能阻止 JS 直接读取 cookie。  
- 已知绕过案例较少但存在（例如极老的浏览器漏洞 CVE-2012-0053、某些 phpinfo 泄露/页面回显、Flash/Java 插件交互等），因此 HttpOnly 只是降低风险的手段之一。  
- 结合 `Secure`、`SameSite` 与短会话时长使用，能进一步强化安全性。

参考： https://blog.csdn.net/weixin_42478365/article/details/116597222

---

## 三、XSS Filter（基于过滤/实体化的防护）

**思路**：在服务端或前端检查并处理用户输入，针对危险字符（如 `<`, `>`, `'`, `"` 等）进行实体化或移除危险片段。

**实现方式**：

- 最简单的：对输出做上下文相关编码（HTML encode / Attribute encode / JS encode / URL encode）。  
- 过滤器：对输入做黑名单或白名单过滤（推荐白名单）。  
- 使用成熟库或框架的自动转义能力（例如模板引擎内置的转义功能）。

**实验与绕过示例**（来自靶场/实战）：

1. **无过滤**：`<script>alert()</script>`  
2. **部分实体化/回显**：`"> <script>alert()</script> <"`  
3. **全部实体化但事件属性可用**：`' onfocus=javascript:alert() '`  
4. **采用大小写绕过匹配**：`"> <sCript>alert()</sCript> <"`  
5. **字符双写/混淆绕过**：`"> <a hrehreff=javasscriptcript:alert()>x</a> <"`  
6. **Unicode/实体编码绕过**：`&#x006a&#x0061&#x0076&#x0061&#x0073&#x0063&#x0072&#x0069&#x0070&#x0074&#x003a&#x0061&#x006c&#x0065&#x0072&#x0074&#x0028&#x0029`（拼接 javascript:alert()）  
7. **属性闭合利用**：`?t_sort=" onfocus=javascript:alert() type="text`

更多绕过技巧与案例：

- XSS-Lab（靶场）：https://github.com/Re13orn/xss-lab  
- 绕过与检测工具：XSStrike — https://github.com/s0md3v/XSStrike  
- 技术博客： https://xz.aliyun.com/t/4067

---

## 黑盒 XSS 手工分析（思路）

1. 在页面中找所有显示（回显）的数据点（包括隐藏字段与动态注入点）。  
2. 在这些点注入 JS payload，观察哪些能执行。  
3. 若不能执行，分析为何（被实体化、被引号包裹、关键词被过滤等），并据此调整 payload。  
4. 记录测试过程、截图与响应，便于报告与修复。

---

## 小结与建议

- **优先级**：最稳健的组合是：正确的上下文输出编码 + HttpOnly + 严格 CSP（按业务允许最小化脚本来源）。  
- **不要单靠过滤器**：输入过滤/黑名单易被绕过，必须结合输出编码与浏览器策略（CSP）。  
- **测试流程化**：使用靶场与自动化工具（Burp、XSStrike）结合手工测试，确保高覆盖率。

---